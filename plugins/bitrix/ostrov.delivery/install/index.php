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
        $this->createOrderProperty();

        return true;
    }

    public function DoUninstall()
    {
        $this->unregisterEvents();
        UnRegisterModule($this->MODULE_ID);

        return true;
    }

    private function createOrderProperty(): void
    {
        if (!Loader::includeModule('sale')) {
            return;
        }

        // Check if property already exists
        $dbRes = \Bitrix\Sale\Internals\OrderPropsTable::getList([
            'filter' => ['CODE' => 'OSTROV_ORDER_ID'],
            'limit' => 1,
        ]);

        if ($dbRes->fetch()) {
            return; // Already exists
        }

        // Get default person type (first available)
        $personTypeRes = \Bitrix\Sale\Internals\PersonTypeTable::getList([
            'order' => ['ID' => 'ASC'],
            'limit' => 1,
        ]);
        $personType = $personTypeRes->fetch();
        if (!$personType) {
            return;
        }

        // Get property group (first available or create)
        $groupRes = \Bitrix\Sale\Internals\OrderPropsGroupTable::getList([
            'filter' => ['PERSON_TYPE_ID' => $personType['ID']],
            'order' => ['ID' => 'ASC'],
            'limit' => 1,
        ]);
        $group = $groupRes->fetch();

        \Bitrix\Sale\Internals\OrderPropsTable::add([
            'PERSON_TYPE_ID' => $personType['ID'],
            'NAME' => 'Ostrov Order ID',
            'CODE' => 'OSTROV_ORDER_ID',
            'TYPE' => 'STRING',
            'REQUIRED' => 'N',
            'USER_PROPS' => 'N',
            'IS_LOCATION' => 'N',
            'IS_LOCATION4TAX' => 'N',
            'IS_PROFILE_NAME' => 'N',
            'IS_PAYER' => 'N',
            'IS_EMAIL' => 'N',
            'IS_PHONE' => 'N',
            'IS_ZIP' => 'N',
            'IS_ADDRESS' => 'N',
            'ACTIVE' => 'Y',
            'UTIL' => 'Y', // Hidden from user, system property
            'SORT' => 900,
            'PROPS_GROUP_ID' => $group ? $group['ID'] : 1,
        ]);
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
