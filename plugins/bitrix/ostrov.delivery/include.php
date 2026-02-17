<?php
use Bitrix\Main\Loader;

Loader::registerAutoLoadClasses('ostrov.delivery', [
    'Ostrov\\Delivery\\Service\\ApiClient' => 'lib/Service/ApiClient.php',
    'Ostrov\\Delivery\\Service\\OrderExporter' => 'lib/Service/OrderExporter.php',
    'Ostrov\\Delivery\\Mapper\\OrderMapper' => 'lib/Mapper/OrderMapper.php',
    'Ostrov\\Delivery\\Event\\SaleEvents' => 'lib/Event/SaleEvents.php',
    'Ostrov\\Delivery\\Logger\\Logger' => 'lib/Logger/Logger.php',
]);
