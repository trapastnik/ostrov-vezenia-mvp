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

        if (empty($payload['recipient']['postal_code']) || empty($payload['items'])) {
            Logger::error('Order export skipped: missing recipient postal_code or items', ['order_id' => $order->getId()]);
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
