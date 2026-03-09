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
        $this->InstallFiles();
        $this->registerEvents();
        $this->createOrderProperty();
        $this->createPassportProperties();
        $this->registerDeliveryService();

        return true;
    }

    public function DoUninstall()
    {
        $this->unregisterDeliveryService();
        $this->unregisterEvents();
        $this->UnInstallFiles();
        UnRegisterModule($this->MODULE_ID);

        return true;
    }

    public function InstallFiles(): bool
    {
        $srcDir = __DIR__ . '/components';
        $dstDir = $_SERVER['DOCUMENT_ROOT'] . '/bitrix/components';

        if (is_dir($srcDir)) {
            CopyDirFiles($srcDir, $dstDir, true, true);
        }

        return true;
    }

    public function UnInstallFiles(): bool
    {
        $componentDir = $_SERVER['DOCUMENT_ROOT'] . '/bitrix/components/ostrov';
        if (is_dir($componentDir)) {
            Directory::deleteDirectory($componentDir);
        }

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
            'ENTITY_REGISTRY_TYPE' => 'ORDER',
            'ENTITY_TYPE' => 'ORDER',
        ]);
    }

    /**
     * Creates passport properties required for customs declarations.
     * Passport series and number are mandatory for international shipments from Kaliningrad.
     */
    private function createPassportProperties(): void
    {
        if (!Loader::includeModule('sale')) {
            return;
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

        // Get first property group for personal data
        $groupRes = \Bitrix\Sale\Internals\OrderPropsGroupTable::getList([
            'filter' => ['PERSON_TYPE_ID' => $personType['ID']],
            'order' => ['ID' => 'ASC'],
            'limit' => 1,
        ]);
        $group = $groupRes->fetch();
        $groupId = $group ? $group['ID'] : 1;

        $passportProps = [
            [
                'CODE' => 'PASSPORT_SERIES',
                'NAME' => 'Серия паспорта',
                'DESCRIPTION' => 'Для таможенного оформления (4 цифры)',
                'SORT' => 700,
            ],
            [
                'CODE' => 'PASSPORT_NUMBER',
                'NAME' => 'Номер паспорта',
                'DESCRIPTION' => 'Для таможенного оформления (6 цифр)',
                'SORT' => 710,
            ],
        ];

        foreach ($passportProps as $propDef) {
            // Check if property already exists
            $dbRes = \Bitrix\Sale\Internals\OrderPropsTable::getList([
                'filter' => ['CODE' => $propDef['CODE'], 'PERSON_TYPE_ID' => $personType['ID']],
                'limit' => 1,
            ]);

            if ($dbRes->fetch()) {
                continue; // Already exists
            }

            \Bitrix\Sale\Internals\OrderPropsTable::add([
                'PERSON_TYPE_ID' => $personType['ID'],
                'NAME' => $propDef['NAME'],
                'CODE' => $propDef['CODE'],
                'TYPE' => 'STRING',
                'REQUIRED' => 'Y',
                'USER_PROPS' => 'Y',
                'IS_LOCATION' => 'N',
                'IS_LOCATION4TAX' => 'N',
                'IS_PROFILE_NAME' => 'N',
                'IS_PAYER' => 'N',
                'IS_EMAIL' => 'N',
                'IS_PHONE' => 'N',
                'IS_ZIP' => 'N',
                'IS_ADDRESS' => 'N',
                'ACTIVE' => 'Y',
                'UTIL' => 'N',
                'DESCRIPTION' => $propDef['DESCRIPTION'] ?? '',
                'SORT' => $propDef['SORT'],
                'PROPS_GROUP_ID' => $groupId,
                'ENTITY_REGISTRY_TYPE' => 'ORDER',
                'ENTITY_TYPE' => 'ORDER',
            ]);
        }
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
        $eventManager->registerEventHandler(
            'sale',
            'onSaleDeliveryHandlersClassNamesBuildList',
            $this->MODULE_ID,
            'Ostrov\\Delivery\\Event\\SaleEvents',
            'onSaleDeliveryHandlersClassNamesBuildList'
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
        $eventManager->unRegisterEventHandler(
            'sale',
            'onSaleDeliveryHandlersClassNamesBuildList',
            $this->MODULE_ID,
            'Ostrov\\Delivery\\Event\\SaleEvents',
            'onSaleDeliveryHandlersClassNamesBuildList'
        );
    }

    private function registerDeliveryService(): void
    {
        if (!Loader::includeModule('sale')) {
            return;
        }

        // Ensure our autoloader is registered so OstrovHandler class is available
        Loader::includeModule($this->MODULE_ID);

        // Check if already registered
        $existing = \Bitrix\Sale\Delivery\Services\Table::getList([
            'filter' => ['=CLASS_NAME' => '\\Ostrov\\Delivery\\Delivery\\OstrovHandler'],
            'limit' => 1,
        ]);

        if ($existing->fetch()) {
            return;
        }

        // Register delivery service via direct table insert
        // Manager::add() validates CLASS_NAME exists which may fail during install
        $result = \Bitrix\Sale\Delivery\Services\Table::add([
            'NAME' => 'Остров Везения',
            'ACTIVE' => 'Y',
            'DESCRIPTION' => 'Почта России + таможенное оформление (Калининград)',
            'CLASS_NAME' => '\\Ostrov\\Delivery\\Delivery\\OstrovHandler',
            'CURRENCY' => 'RUB',
            'SORT' => 100,
        ]);

        if (!$result->isSuccess()) {
            // Non-fatal: log but don't block module installation
            // Service can be added manually via Bitrix admin
        }
    }

    private function unregisterDeliveryService(): void
    {
        if (!Loader::includeModule('sale')) {
            return;
        }

        $dbRes = \Bitrix\Sale\Delivery\Services\Table::getList([
            'filter' => ['=CLASS_NAME' => '\\Ostrov\\Delivery\\Delivery\\OstrovHandler'],
        ]);

        while ($row = $dbRes->fetch()) {
            \Bitrix\Sale\Delivery\Services\Manager::delete($row['ID']);
        }
    }
}
