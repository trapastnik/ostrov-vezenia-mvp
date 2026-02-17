<?php

namespace Ostrov\Delivery\Logger;

use Bitrix\Main\Diag\Debug;

class Logger
{
    public static function info(string $message, array $context = []): void
    {
        Debug::writeToFile(['message' => $message, 'context' => $context], 'ostrov.delivery', '/bitrix/logs/ostrov_delivery.log');
    }

    public static function error(string $message, array $context = []): void
    {
        Debug::writeToFile(['level' => 'error', 'message' => $message, 'context' => $context], 'ostrov.delivery', '/bitrix/logs/ostrov_delivery.log');
    }
}
