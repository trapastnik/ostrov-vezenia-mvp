import base64
from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass
class TariffResult:
    cost_kopecks: int
    vat_kopecks: int
    total_kopecks: int
    min_days: int
    max_days: int


@dataclass
class TariffCompareResult:
    public_cost_kopecks: int
    public_vat_kopecks: int
    public_total_kopecks: int
    contract_cost_kopecks: int
    contract_vat_kopecks: int
    contract_total_kopecks: int
    savings_kopecks: int
    savings_percent: float
    min_days: int
    max_days: int
    contract_available: bool
    contract_error: str | None


@dataclass
class AddressResult:
    index: str
    region: str
    place: str
    street: str
    house: str
    room: str
    quality_code: str
    validation_code: str
    is_valid: bool


@dataclass
class FioResult:
    surname: str
    name: str
    middle_name: str
    quality_code: str


@dataclass
class PhoneResult:
    country_code: str
    city_code: str
    number: str
    quality_code: str


GOOD_QUALITY_CODES = {"GOOD", "POSTAL_BOX", "ON_DEMAND", "UNDEF_05"}
GOOD_VALIDATION_CODES = {"VALIDATED", "OVERRIDDEN", "CONFIRMED_MANUALLY"}


class PochtaClient:
    BASE_URL = "https://otpravka-api.pochta.ru/1.0"
    POSTOFFICE_URL = "https://otpravka-api.pochta.ru/postoffice/1.0"
    PUBLIC_TARIFF_URL = "https://tariff.pochta.ru/v2"

    def __init__(self, settings: Settings):
        self._api_token = settings.POCHTA_API_TOKEN
        self._login = settings.POCHTA_LOGIN
        self._password = settings.POCHTA_PASSWORD
        self._client: httpx.AsyncClient | None = None

    def _auth_headers(self) -> dict[str, str]:
        user_auth = base64.b64encode(f"{self._login}:{self._password}".encode()).decode()
        return {
            "Authorization": f"AccessToken {self._api_token}",
            "X-User-Authorization": f"Basic {user_auth}",
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json;charset=UTF-8",
        }

    async def start(self):
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def calculate_tariff_public(
        self, index_from: str, index_to: str, weight_grams: int, object_code: int = 23030
    ) -> TariffResult:
        params = {
            "json": "",
            "object": object_code,
            "from": index_from,
            "to": index_to,
            "weight": weight_grams,
            "pack": 10,
        }
        resp = await self._client.get(f"{self.PUBLIC_TARIFF_URL}/calculate/tariff/delivery", params=params)
        resp.raise_for_status()
        data = resp.json()

        pay = data.get("pay", 0)
        paynds = data.get("paynds", 0)
        delivery = data.get("delivery", {})

        return TariffResult(
            cost_kopecks=pay,
            vat_kopecks=paynds - pay,
            total_kopecks=paynds,
            min_days=delivery.get("min", 0),
            max_days=delivery.get("max", 0),
        )

    async def calculate_tariff_contract(
        self, index_from: str, index_to: str, weight_grams: int, mail_type: str = "ONLINE_PARCEL"
    ) -> TariffResult:
        payload = {
            "index-from": index_from,
            "index-to": index_to,
            "mail-category": "ORDINARY",
            "mail-type": mail_type,
            "mass": weight_grams,
            "payment-method": "CASHLESS",
        }
        resp = await self._client.post(f"{self.BASE_URL}/tariff", headers=self._auth_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()

        total_rate = data.get("total-rate", 0)
        total_vat = data.get("total-vat", 0)
        delivery_time = data.get("delivery-time", {})

        return TariffResult(
            cost_kopecks=total_rate,
            vat_kopecks=total_vat,
            total_kopecks=total_rate + total_vat,
            min_days=delivery_time.get("min-days", 0),
            max_days=delivery_time.get("max-days", 0),
        )

    async def normalize_address(self, address: str) -> AddressResult:
        payload = [{"id": "0", "original-address": address}]
        resp = await self._client.post(f"{self.BASE_URL}/clean/address", headers=self._auth_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()[0]

        quality = data.get("quality-code", "")
        validation = data.get("validation-code", "")
        is_valid = quality in GOOD_QUALITY_CODES and validation in GOOD_VALIDATION_CODES

        return AddressResult(
            index=data.get("index", ""),
            region=data.get("region", ""),
            place=data.get("place", ""),
            street=data.get("street", ""),
            house=data.get("house", ""),
            room=data.get("room", ""),
            quality_code=quality,
            validation_code=validation,
            is_valid=is_valid,
        )

    async def normalize_fio(self, fio: str) -> FioResult:
        payload = [{"id": "0", "original-fio": fio}]
        resp = await self._client.post(f"{self.BASE_URL}/clean/physical", headers=self._auth_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()[0]

        return FioResult(
            surname=data.get("surname", ""),
            name=data.get("name", ""),
            middle_name=data.get("middle-name", ""),
            quality_code=data.get("quality-code", ""),
        )

    async def normalize_phone(self, phone: str) -> PhoneResult:
        payload = [{"id": "0", "original-phone": phone}]
        resp = await self._client.post(f"{self.BASE_URL}/clean/phone", headers=self._auth_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()[0]

        return PhoneResult(
            country_code=data.get("phone-country-code", ""),
            city_code=data.get("phone-city-code", ""),
            number=data.get("phone-number", ""),
            quality_code=data.get("quality-code", ""),
        )

    async def get_balance(self) -> int | None:
        """Возвращает баланс в копейках или None если эндпоинт недоступен (нет договора)."""
        resp = await self._client.get(f"{self.BASE_URL}/counterpart/balance", headers=self._auth_headers())
        if resp.status_code == 500:
            # Почта возвращает 500 "No endpoint" для аккаунтов без договора на отправку
            data = resp.json()
            if data.get("sub-code") == "INTERNAL_ERROR" and "No endpoint" in data.get("desc", ""):
                return None
        resp.raise_for_status()
        return resp.json().get("balance", 0)

    async def compare_tariffs(
        self, index_from: str, index_to: str, weight_grams: int, object_code: int = 23030, mail_type: str = "ONLINE_PARCEL"
    ) -> TariffCompareResult:
        public = await self.calculate_tariff_public(index_from, index_to, weight_grams, object_code)

        contract_cost = 0
        contract_vat = 0
        contract_total = 0
        contract_available = False
        contract_error = None
        try:
            contract = await self.calculate_tariff_contract(index_from, index_to, weight_grams, mail_type)
            contract_cost = contract.cost_kopecks
            contract_vat = contract.vat_kopecks
            contract_total = contract.total_kopecks
            contract_available = True
        except Exception as e:
            contract_error = str(e)

        savings_kopecks = public.total_kopecks - contract_total if contract_available else 0
        savings_percent = (savings_kopecks / public.total_kopecks * 100) if contract_available and public.total_kopecks > 0 else 0.0

        return TariffCompareResult(
            public_cost_kopecks=public.cost_kopecks,
            public_vat_kopecks=public.vat_kopecks,
            public_total_kopecks=public.total_kopecks,
            contract_cost_kopecks=contract_cost,
            contract_vat_kopecks=contract_vat,
            contract_total_kopecks=contract_total,
            savings_kopecks=savings_kopecks,
            savings_percent=round(savings_percent, 1),
            min_days=public.min_days,
            max_days=public.max_days,
            contract_available=contract_available,
            contract_error=contract_error,
        )
