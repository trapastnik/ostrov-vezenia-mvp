<?php

namespace Ostrov\Delivery\Event;

use Bitrix\Main\Event;
use Bitrix\Main\EventResult;
use Bitrix\Sale\Order;
use Ostrov\Delivery\Logger\Logger;
use Ostrov\Delivery\Service\OrderExporter;

class SaleEvents
{
    /**
     * Register OstrovHandler class for Bitrix delivery system autoloading.
     * Without this, checkout cannot find/load the custom delivery handler class.
     */
    public static function onSaleDeliveryHandlersClassNamesBuildList(): EventResult
    {
        return new EventResult(
            EventResult::SUCCESS,
            [
                '\\Ostrov\\Delivery\\Delivery\\OstrovHandler' =>
                    '/bitrix/modules/ostrov.delivery/lib/Delivery/OstrovHandler.php',
            ],
            'ostrov.delivery'
        );
    }

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
