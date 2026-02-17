"""
Тестовый эмулятор заказов — полный цикл работы системы.

Запуск:
    python -m tests.test_emulator

Что делает:
    1. Логин как admin
    2. Создание тестового магазина
    3. Расчёт стоимости доставки (от имени магазина)
    4. Создание нескольких тестовых заказов
    5. Просмотр заказов из админки
    6. Смена статусов заказов по цепочке
    7. Просмотр истории заказа
    8. Вывод результатов
"""

import asyncio
import random
import sys

import httpx

BASE_URL = "http://localhost:8000/api/v1"

# Тестовые данные получателей
RECIPIENTS = [
    {"name": "Иванов Пётр Сергеевич", "phone": "+79261234567", "email": "ivanov@test.ru", "address": "Москва, ул. Ленина, д. 1, кв. 5", "postal_code": "101000"},
    {"name": "Петрова Анна Викторовна", "phone": "+79161112233", "email": "petrova@test.ru", "address": "Санкт-Петербург, Невский пр-кт, д. 28, кв. 12", "postal_code": "190000"},
    {"name": "Сидоров Алексей Дмитриевич", "phone": "+79031234567", "email": "sidorov@test.ru", "address": "Новосибирск, ул. Красный проспект, д. 50", "postal_code": "630000"},
    {"name": "Козлова Мария Александровна", "phone": "+79851112233", "email": "kozlova@test.ru", "address": "Екатеринбург, ул. Малышева, д. 15, кв. 3", "postal_code": "620000"},
    {"name": "Волков Дмитрий Игоревич", "phone": "+79111234567", "email": "volkov@test.ru", "address": "Казань, ул. Баумана, д. 44", "postal_code": "420000"},
]

# Тестовые товары
PRODUCTS = [
    {"name": "KALLAX Стеллаж белый", "price_kopecks": 499900, "weight_grams": 12000},
    {"name": "MALM Комод 4 ящика", "price_kopecks": 899900, "weight_grams": 25000},
    {"name": "POÄNG Кресло", "price_kopecks": 649900, "weight_grams": 8000},
    {"name": "LACK Столик придиванный", "price_kopecks": 99900, "weight_grams": 3500},
    {"name": "KLIPPAN Чехол для дивана", "price_kopecks": 299900, "weight_grams": 2000},
    {"name": "HEMNES Зеркало", "price_kopecks": 349900, "weight_grams": 5000},
    {"name": "BRIMNES Кровать", "price_kopecks": 1299900, "weight_grams": 28000},
    {"name": "ALEX Тумба с ящиками", "price_kopecks": 599900, "weight_grams": 15000},
]

STATUS_CHAIN = [
    "awaiting_pickup",
    "received_warehouse",
]


def ok(msg: str):
    print(f"  [OK] {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")


def section(msg: str):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:

        # ── 1. Логин ──
        section("1. Логин администратора")
        resp = await client.post("/auth/login", json={"email": "admin@ostrov.ru", "password": "admin123"})
        if resp.status_code != 200:
            fail(f"Логин не удался: {resp.status_code} {resp.text}")
            print("\n  Создайте admin-пользователя:")
            print("  docker compose exec backend python -m app.scripts.create_admin")
            print("  Email: admin@ostrov.ru, Password: admin123")
            sys.exit(1)

        token_data = resp.json()
        admin_token = token_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        ok(f"Вошли как {token_data['operator']['name']} ({token_data['operator']['role']})")

        # ── 2. Создание тестового магазина ──
        section("2. Создание тестового магазина")
        resp = await client.post(
            "/admin/shops",
            json={
                "name": "IKEA-39 Тест",
                "domain": f"test-ikea-{random.randint(1000, 9999)}.ru",
                "customs_fee_kopecks": 25000,
                "sender_postal_code": "238311",
            },
            headers=admin_headers,
        )
        if resp.status_code == 201:
            shop = resp.json()
            api_key = shop["api_key"]
            shop_id = shop["id"]
            ok(f"Магазин создан: {shop['name']} (domain: {shop['domain']})")
            ok(f"API ключ: {api_key[:16]}...")
        else:
            fail(f"Не удалось создать магазин: {resp.status_code} {resp.text}")
            sys.exit(1)

        shop_headers = {"X-API-Key": api_key}

        # ── 3. Расчёт стоимости доставки ──
        section("3. Расчёт стоимости доставки")
        for recipient in RECIPIENTS[:3]:
            product = random.choice(PRODUCTS)
            resp = await client.post(
                "/delivery/calculate",
                json={
                    "postal_code": recipient["postal_code"],
                    "weight_grams": product["weight_grams"],
                    "total_amount_kopecks": product["price_kopecks"],
                },
                headers=shop_headers,
            )
            if resp.status_code == 200:
                calc = resp.json()
                if calc["available"]:
                    ok(
                        f"{recipient['address'][:30]}... → "
                        f"доставка: {calc['delivery_cost_kopecks']/100:.0f} руб, "
                        f"таможня: {calc['customs_fee_kopecks']/100:.0f} руб, "
                        f"итого: {calc['total_cost_kopecks']/100:.0f} руб, "
                        f"срок: {calc['delivery_days_min']}-{calc['delivery_days_max']} дн."
                    )
                else:
                    ok(f"Доставка недоступна: {calc['rejection_reason']}")
            else:
                fail(f"Ошибка расчёта: {resp.status_code} {resp.text}")

        # ── 4. Создание заказов ──
        section("4. Создание тестовых заказов")
        order_ids = []
        for i, recipient in enumerate(RECIPIENTS):
            items = random.sample(PRODUCTS, k=random.randint(1, 3))
            items_data = [
                {"name": p["name"], "quantity": 1, "price_kopecks": p["price_kopecks"], "weight_grams": p["weight_grams"]}
                for p in items
            ]

            # Проверяем лимит 200$ (~1.85M копеек)
            total = sum(item["price_kopecks"] for item in items_data)
            total_weight = sum(item["weight_grams"] for item in items_data)
            if total > 1800000 or total_weight > 30000:
                items_data = [items_data[0]]  # берём только первый товар

            resp = await client.post(
                "/orders",
                json={
                    "external_order_id": f"IKEA-ORD-{1000 + i}",
                    "recipient": recipient,
                    "items": items_data,
                },
                headers=shop_headers,
            )
            if resp.status_code == 201:
                order = resp.json()
                order_ids.append(order["id"])
                ok(
                    f"Заказ {order['external_order_id']}: "
                    f"{recipient['name']} → {recipient['address'][:25]}... "
                    f"({order['total_amount_kopecks']/100:.0f} руб, "
                    f"доставка: {order['delivery_cost_kopecks']/100:.0f} руб)"
                )
            else:
                fail(f"Ошибка создания заказа: {resp.status_code} {resp.text}")

        if not order_ids:
            fail("Нет созданных заказов, прерываем тест")
            sys.exit(1)

        # ── 5. Просмотр заказов из админки ──
        section("5. Просмотр заказов из админки")
        resp = await client.get("/admin/orders", headers=admin_headers, params={"per_page": 50})
        if resp.status_code == 200:
            data = resp.json()
            ok(f"Всего заказов в системе: {data['total']}")
            for o in data["items"][:5]:
                ok(f"  {o['external_order_id']} | {o['recipient_name']} | {o['status']}")
        else:
            fail(f"Ошибка: {resp.status_code}")

        # ── 6. Смена статусов ──
        section("6. Проведение заказов по статусам")
        for order_id in order_ids[:3]:
            for new_status in STATUS_CHAIN:
                resp = await client.patch(
                    f"/admin/orders/{order_id}/status",
                    json={"status": new_status, "comment": f"Тест: переход в {new_status}"},
                    headers=admin_headers,
                )
                if resp.status_code == 200:
                    order = resp.json()
                    ok(f"Заказ {order['external_order_id']}: → {new_status}")
                else:
                    fail(f"Ошибка смены статуса: {resp.status_code} {resp.text}")

        # ── 7. Просмотр истории заказа ──
        section("7. История первого заказа")
        if order_ids:
            resp = await client.get(f"/admin/orders/{order_ids[0]}", headers=admin_headers)
            if resp.status_code == 200:
                tracking = resp.json()
                ok(f"Заказ {tracking['id'][:8]}..., текущий статус: {tracking['status']}")
                for entry in tracking["history"]:
                    comment = f" ({entry['comment']})" if entry.get("comment") else ""
                    ok(f"  {entry['created_at'][:19]} | {entry['old_status'] or '—'} → {entry['new_status']}{comment}")

        # ── 8. Проверка API магазина (статус и трекинг) ──
        section("8. API магазина: проверка статуса заказа")
        if order_ids:
            resp = await client.get(f"/orders/{order_ids[0]}/status", headers=shop_headers)
            if resp.status_code == 200:
                status_data = resp.json()
                ok(f"Статус: {status_data['status']}, трек: {status_data['track_number'] or 'нет'}")

            resp = await client.get(f"/orders/{order_ids[0]}/tracking", headers=shop_headers)
            if resp.status_code == 200:
                tracking = resp.json()
                ok(f"История: {len(tracking['history'])} записей")

        # ── Итог ──
        section("ТЕСТ ЗАВЕРШЁН")
        print(f"\n  Создано заказов: {len(order_ids)}")
        print(f"  Магазин: {shop['name']} ({shop['domain']})")
        print(f"  API ключ: {api_key}")
        print(f"\n  Откройте админ-панель: http://localhost:3000")
        print(f"  Логин: admin@ostrov.ru / admin123")
        print()


if __name__ == "__main__":
    asyncio.run(main())
