"""
Маршрутизация посылок по хабам на основе почтового индекса получателя.

Логика: первые 3 цифры индекса определяют регион → регион маппируется на хаб.
Хаб = точка консолидации на магистральном участке.
"""

# Справочник хабов
HUB_REGISTRY = {
    "msk": {
        "name": "Москва",
        "transport": "truck",
        "regions": list(range(100, 135)) + list(range(140, 143)) + list(range(143, 146)),
    },
    "spb": {
        "name": "Санкт-Петербург",
        "transport": "air",
        "regions": list(range(188, 200)),
    },
    "ekb": {
        "name": "Екатеринбург",
        "transport": "truck",
        "regions": list(range(620, 625)) + list(range(623, 628)),
    },
    "nsk": {
        "name": "Новосиbirск",
        "transport": "air",
        "regions": list(range(630, 636)),
    },
    "krd": {
        "name": "Краснодар",
        "transport": "truck",
        "regions": list(range(350, 356)) + list(range(353, 355)),
    },
    "niz": {
        "name": "Нижний Новгород",
        "transport": "truck",
        "regions": list(range(603, 608)),
    },
    "kzn": {
        "name": "Казань",
        "transport": "truck",
        "regions": list(range(420, 423)) + list(range(422, 424)),
    },
    "rnd": {
        "name": "Ростов-на-Дону",
        "transport": "truck",
        "regions": list(range(344, 347)),
    },
    "smr": {
        "name": "Самара",
        "transport": "truck",
        "regions": list(range(443, 447)),
    },
    "ufa": {
        "name": "Уфа",
        "transport": "truck",
        "regions": list(range(450, 454)),
    },
}

# Построим плоский словарь: prefix (int) → hub_code
_PREFIX_TO_HUB: dict[int, str] = {}
for _hub_code, _hub_info in HUB_REGISTRY.items():
    for _region_prefix in _hub_info["regions"]:
        _PREFIX_TO_HUB[_region_prefix] = _hub_code


def get_hub_for_postal_code(postal_code: str) -> str:
    """
    Возвращает код хаба для почтового индекса.
    Если хаб не найден — возвращает 'msk' (Москва как дефолтный хаб).
    """
    try:
        prefix = int(postal_code[:3])
        return _PREFIX_TO_HUB.get(prefix, "msk")
    except (ValueError, IndexError):
        return "msk"
