<?php

namespace Ostrov\Delivery\Event;

use Bitrix\Main\Event;
use Bitrix\Sale\Order;
use Ostrov\Delivery\Logger\Logger;
use Ostrov\Delivery\Service\OrderExporter;

class SaleEvents
{
    public static function onSaleOrderSaved(Event $event): void
    {
        $isNew = (bool)$event->getParameter('IS_NEW');
        if (!$isNew) {
            return;
        }

        /** @var Order|null $order */
        $order = $event->getParameter('ENTITY');
        if (!$order instanceof Order) {
            return;
        }

        try {
            (new OrderExporter())->export($order);
        } catch (\Throwable $e) {
            Logger::error('Order export failed', [
                'order_id' => $order->getId(),
                'message' => $e->getMessage(),
            ]);
        }
    }
}
