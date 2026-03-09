# ostrov.delivery — Модуль доставки для 1С-Битрикс

Модуль интеграции интернет-магазина на 1С-Битрикс с сервисом «Остров Везения».
Добавляет службу доставки «Почта России + таможенное оформление» в checkout и автоматически экспортирует заказы в систему Остров.

**Версия:** 0.3.0
**Совместимость:** 1С-Битрикс (коробка) с модулем `sale`. Не работает на Bitrix24 SaaS (облако).

---

## Что делает модуль

| Функция | Описание |
|---------|----------|
| Расчёт доставки | В checkout показывает стоимость доставки (Почта России + таможня) через Ostrov API |
| Автоэкспорт заказов | При создании заказа автоматически отправляет его в систему Остров |
| Паспортные данные | Добавляет обязательные поля «Серия паспорта» и «Номер паспорта» в форму оформления (для таможни) |
| Хранение ID | Сохраняет ID заказа в системе Остров в свойстве заказа `OSTROV_ORDER_ID` |

---

## Структура файлов

```
ostrov.delivery/
├── install/
│   ├── index.php                # Инсталлятор: регистрация модуля, событий, свойств, службы доставки
│   └── version.php              # Версия модуля
├── include.php                  # Автозагрузка классов (Loader::registerAutoLoadClasses)
├── options.php                  # Страница настроек модуля
├── admin/
│   └── settings.php             # Обёртка для страницы настроек в админке Битрикс
├── lib/
│   ├── Delivery/
│   │   └── OstrovHandler.php    # Служба доставки (extends Bitrix\Sale\Delivery\Services\Base)
│   ├── Event/
│   │   └── SaleEvents.php       # Обработчики событий sale
│   ├── Mapper/
│   │   └── OrderMapper.php      # Маппинг заказа Битрикс → Ostrov API payload
│   ├── Service/
│   │   ├── ApiClient.php        # HTTP-клиент к Ostrov API (Bitrix\Main\Web\HttpClient)
│   │   ├── DeliveryCalculator.php # Расчёт стоимости доставки через API
│   │   └── OrderExporter.php    # Экспорт заказа в Ostrov + валидация обязательных полей
│   └── Logger/
│       └── Logger.php           # Логирование в /bitrix/logs/ostrov_delivery.log
└── README.md
```

---

## Установка

### Требования

- 1С-Битрикс (коробочная версия) с доступом к файловой системе
- PHP 8.0+
- Модуль `sale` (Интернет-магазин) — активен
- Доступ к API Остров Везения (URL + API-ключ)

### Шаг 1. Копирование файлов

Скопировать папку `ostrov.delivery` в директорию модулей Битрикса:

```bash
cp -r ostrov.delivery /path/to/bitrix/modules/ostrov.delivery
```

### Шаг 2. Установка модуля

Админка Битрикс → **Marketplace** → **Установленные решения** → Найти «Ostrov Delivery» → **Установить**

При установке модуль автоматически:

1. **Регистрирует обработчики событий:**
   - `OnSaleOrderSaved` — автоэкспорт новых заказов в Ostrov API
   - `onSaleDeliveryHandlersClassNamesBuildList` — регистрация класса службы доставки для автозагрузки в checkout

2. **Создаёт свойства заказа** (через `OrderPropsTable::add`, стандартный D7 API):
   - `OSTROV_ORDER_ID` — системное (скрытое), хранит ID заказа в системе Остров
   - `PASSPORT_SERIES` — серия паспорта (обязательное, видимое в checkout)
   - `PASSPORT_NUMBER` — номер паспорта (обязательное, видимое в checkout)

3. **Регистрирует службу доставки** «Остров Везения» в таблице `b_sale_delivery_srv`

> **Никакие файлы Битрикса не модифицируются.** Модуль работает только через стандартные API: EventManager, OrderPropsTable, Delivery\Services\Table.

### Шаг 3. Настройка подключения к API

Админка Битрикс → **Настройки** → **Настройки продукта** → **Настройки модулей** → **Ostrov Delivery**

| Параметр | Описание | Пример |
|----------|----------|--------|
| API Base URL | Адрес API Остров Везения | `https://api.ostrov-vezeniya.ru` |
| X-API-Key | Ключ магазина (выдаётся в админке Остров) | `sk-abc123...` |
| Timeout | Таймаут HTTP-запросов (секунды) | `10` |

### Шаг 4. Проверка

1. Перейти в каталог магазина, добавить товар в корзину
2. На странице оформления заказа должна появиться служба доставки **«Остров Везения»** с рассчитанной стоимостью
3. Должны отображаться поля **«Серия паспорта»** и **«Номер паспорта»**
4. После оформления заказа — проверить лог `/bitrix/logs/ostrov_delivery.log`

---

## Как это работает

### Расчёт доставки в checkout

```
Покупатель вводит индекс
  → OstrovHandler::calculateConcrete()
    → DeliveryCalculator::calculate()
      → ApiClient::calculateDelivery()
        → POST {api_base_url}/api/v1/delivery/calculate
          { postal_code, weight_grams, total_amount_kopecks }
        ← { available, total_cost_kopecks, delivery_days_min, delivery_days_max }
  → Отображает стоимость и срок в checkout
```

### Автоэкспорт заказа

```
Покупатель оформляет заказ
  → Событие OnSaleOrderSaved (IS_NEW=true)
    → SaleEvents::onSaleOrderSaved()
      → OrderExporter::export()
        → OrderMapper::toOstrovPayload() — собирает данные заказа
        → Валидация: postal_code, items, passport_series (≥4), passport_number (≥6)
        → ApiClient::createOrder()
          → POST {api_base_url}/api/v1/orders { payload }
          ← { id: "ostrov-order-id" }
        → Сохраняет ostrov_order_id в свойство заказа OSTROV_ORDER_ID
```

### Маппинг полей

| Bitrix | Ostrov API |
|--------|-----------|
| `ACCOUNT_NUMBER` | `external_order_id` (с префиксом `BX-`) |
| Свойство `FIO` (IS_PAYER) | `recipient.name` |
| Свойство `PHONE` (IS_PHONE) | `recipient.phone` |
| `USER_EMAIL` | `recipient.email` |
| Свойство `ADDRESS` (IS_ADDRESS) | `recipient.address` |
| Свойство `ZIP` / `POSTAL_CODE` / `INDEX` | `recipient.postal_code` |
| Свойство `PASSPORT_SERIES` | `recipient.passport_series` |
| Свойство `PASSPORT_NUMBER` | `recipient.passport_number` |
| Корзина: `NAME`, `QUANTITY`, `PRICE`, `WEIGHT` | `items[]` (цена в копейках, вес в граммах) |

---

## Удаление

Админка Битрикс → **Marketplace** → **Установленные решения** → «Ostrov Delivery» → **Удалить**

При удалении:
- Удаляются обработчики событий
- Удаляется служба доставки из `b_sale_delivery_srv`
- Модуль выгружается

> Свойства заказов (`OSTROV_ORDER_ID`, `PASSPORT_SERIES`, `PASSPORT_NUMBER`) **не удаляются**, чтобы не потерять данные существующих заказов.

---

## Логирование

Все операции логируются в `/bitrix/logs/ostrov_delivery.log`:

- Расчёт доставки (индекс, вес, стоимость)
- Экспорт заказа (order_id, ostrov_order_id)
- Ошибки API (status code, response body)
- Пропущенные заказы (отсутствующие обязательные поля)

---

## Известные ограничения

- Модуль привязывает свойства к **первому** типу плательщика (`PERSON_TYPE_ID` с минимальным `ID`). Если в магазине несколько типов плательщиков — свойства создадутся только для первого.
- Товары без указанного веса получают дефолтный вес 1000 г (1 кг).
- При недоступности API Остров заказ создаётся в Битриксе, но не экспортируется (ошибка логируется). Retry-механизм пока не реализован.

---

## Техническая заметка: ENTITY_REGISTRY_TYPE

При создании свойств заказа через `OrderPropsTable::add()` **обязательно** указывать `ENTITY_REGISTRY_TYPE => 'ORDER'`. Без этого поля Битриксовый ORM (`\Bitrix\Sale\Property::getList()`) не включит свойство в выборку, и оно не появится в checkout. Это особенность D7 API, не описанная в официальной документации.
