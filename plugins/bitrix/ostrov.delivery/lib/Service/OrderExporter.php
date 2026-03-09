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

        $missing = [];
        if (empty($payload['recipient']['postal_code'])) {
            $missing[] = 'postal_code';
        }
        if (empty($payload['items'])) {
            $missing[] = 'items';
        }
        if (strlen($payload['recipient']['passport_series'] ?? '') < 4) {
            $missing[] = 'passport_series';
        }
        if (strlen($payload['recipient']['passport_number'] ?? '') < 6) {
            $missing[] = 'passport_number';
        }
        if (!empty($missing)) {
            Logger::error('Order export skipped: missing required fields', [
                'order_id' => $order->getId(),
                'missing' => implode(', ', $missing),
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
