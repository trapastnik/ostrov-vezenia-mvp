<?php

use Bitrix\Main\Application;
use Bitrix\Main\EventManager;
use Bitrix\Main\IO\Directory;
use Bitrix\Main\Loader;

class ostrov_delivery extends CModule
{
    public $MODULE_ID = 'ostrov.delivery';
    public $MODULE_NAME = 'Ostrov Delivery';
    public $MODULE_DESCRIPTION = 'Delivery integration with Ostrov API';
    public $PARTNER_NAME = 'Ostrov';
    public $PARTNER_URI = 'https://ostrov-vezeniya.ru';

    public function __construct()
    {
        include __DIR__ . '/version.php';
        $this->MODULE_VERSION = $arModuleVersion['VERSION'];
        $this->MODULE_VERSION_DATE = $arModuleVersion['VERSION_DATE'];
    }

    public function DoInstall()
    {
        global $APPLICATION;

        if (!Loader::includeModule('sale')) {
            $APPLICATION->ThrowException('Module sale is required.');
            return false;
        }

        RegisterModule($this->MODULE_ID);
        $this->registerEvents();

        return true;
    }

    public function DoUninstall()
    {
        $this->unregisterEvents();
        UnRegisterModule($this->MODULE_ID);

        return true;
    }

    private function registerEvents(): void
    {
        $eventManager = EventManager::getInstance();
        $eventManager->registerEventHandler(
            'sale',
            'OnSaleOrderSaved',
            $this->MODULE_ID,
            'Ostrov\\Delivery\\Event\\SaleEvents',
            'onSaleOrderSaved'
        );
    }

    private function unregisterEvents(): void
    {
        $eventManager = EventManager::getInstance();
        $eventManager->unRegisterEventHandler(
            'sale',
            'OnSaleOrderSaved',
            $this->MODULE_ID,
            'Ostrov\\Delivery\\Event\\SaleEvents',
            'onSaleOrderSaved'
        );
    }
}
