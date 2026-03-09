<?php

namespace Ostrov\Delivery\Service;

use Bitrix\Main\Config\Option;
use Bitrix\Sale\Order;
use Ostrov\Delivery\Logger\Logger;
use Ostrov\Delivery\Mapper\OrderMapper;

class OrderExporter
{
    private const MODULE_ID = 'ostrov.delivery';
    private const ORDER_PROP_CODE = 'OSTROV_ORDER_ID';

    public function export(Order $order): void
    {
        $payload = OrderMapper::toOstrovPayload($order);

        $errors = [];

        // Почтовый индекс — 6 цифр
        $postalCode = $payload['recipient']['postal_code'] ?? '';
        if (!preg_match('/^\d{6}$/', $postalCode)) {
            $errors[] = 'postal_code (нужно 6 цифр)';
        }

        // Товары
        if (empty($payload['items'])) {
            $errors[] = 'items (пустой список товаров)';
        }

        // Паспортная серия — ровно 4 цифры
        $passportSeries = $payload['recipient']['passport_series'] ?? '';
        if (!preg_match('/^\d{4}$/', $passportSeries)) {
            $errors[] = 'passport_series (нужно ровно 4 цифры)';
        }

        // Номер паспорта — ровно 6 цифр
        $passportNumber = $payload['recipient']['passport_number'] ?? '';
        if (!preg_match('/^\d{6}$/', $passportNumber)) {
            $errors[] = 'passport_number (нужно ровно 6 цифр)';
        }

        // Адрес — минимум 10 символов
        $address = $payload['recipient']['address'] ?? '';
        if (mb_strlen($address) < 10) {
            $errors[] = 'address (слишком короткий, нужно минимум 10 символов)';
        }

        // Телефон — российский формат
        $phone = $payload['recipient']['phone'] ?? '';
        $phoneDigits = preg_replace('/[\s\-\(\)\+]/', '', $phone);
        if (strlen($phoneDigits) === 11 && $phoneDigits[0] === '8') {
            $phoneDigits = '7' . substr($phoneDigits, 1);
        }
        if (!preg_match('/^7\d{10}$/', $phoneDigits)) {
            $errors[] = 'phone (нужен российский номер +7XXXXXXXXXX)';
        }

        // ФИО — минимум 2 символа
        $name = $payload['recipient']['name'] ?? '';
        if (mb_strlen($name) < 2) {
            $errors[] = 'name (слишком короткое)';
        }

        if (!empty($errors)) {
            Logger::error('Order export skipped: validation errors', [
                'order_id' => $order->getId(),
                'errors' => implode('; ', $errors),
            ]);
            return;
        }

        $client = new ApiClient();
        $result = $client->createOrder($payload);

        if (!empty($result['id'])) {
            $this->saveExternalId($order, (string)$result['id']);
            Logger::info('Order exported to Ostrov', ['order_id' => $order->getId(), 'ostrov_order_id' => $result['id']]);
        }
    }

    private function saveExternalId(Order $order, string $ostrovOrderId): void
    {
        $propertyCollection = $order->getPropertyCollection();
        $prop = $propertyCollection->getItemByOrderPropertyCode(self::ORDER_PROP_CODE);
        if ($prop) {
            $prop->setValue($ostrovOrderId);
            $order->save();
        }
    }
}
