<?php

if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) {
    die();
}

use Bitrix\Main\Loader;
use Bitrix\Sale\Order;
use Ostrov\Delivery\Service\ApiClient;
use Ostrov\Delivery\Logger\Logger;

/**
 * Компонент трекинга заказа в ЛК покупателя.
 *
 * Размещается на странице деталей заказа в личном кабинете.
 * Получает OSTROV_ORDER_ID из свойств заказа и загружает трекинг из API.
 *
 * Параметры:
 *   ORDER_ID — ID заказа в Битрикс (int)
 *
 * Результат ($arResult):
 *   TRACKING — массив с данными трекинга (status, events, track_number и т.д.)
 *   ERROR — текст ошибки (если есть)
 */
class OstrovOrderTrackingComponent extends \CBitrixComponent
{
    private const ORDER_PROP_CODE = 'OSTROV_ORDER_ID';

    public function executeComponent(): void
    {
        if (!Loader::includeModule('ostrov.delivery') || !Loader::includeModule('sale')) {
            $this->arResult['ERROR'] = 'Модуль ostrov.delivery или sale не установлен';
            $this->includeComponentTemplate();
            return;
        }

        $orderId = (int)$this->arParams['ORDER_ID'];
        if ($orderId <= 0) {
            $this->arResult['ERROR'] = 'Не указан ID заказа';
            $this->includeComponentTemplate();
            return;
        }

        try {
            $this->loadTracking($orderId);
        } catch (\Exception $e) {
            Logger::error('Tracking component error', [
                'order_id' => $orderId,
                'error' => $e->getMessage(),
            ]);
            $this->arResult['ERROR'] = 'Не удалось загрузить данные трекинга';
        }

        $this->includeComponentTemplate();
    }

    private function loadTracking(int $orderId): void
    {
        $order = Order::load($orderId);
        if (!$order) {
            $this->arResult['ERROR'] = 'Заказ не найден';
            return;
        }

        // Получаем OSTROV_ORDER_ID из свойств заказа
        $ostrovOrderId = $this->getOstrovOrderId($order);
        if (empty($ostrovOrderId)) {
            $this->arResult['ERROR'] = 'Заказ не отправлен в систему доставки';
            return;
        }

        // Запрашиваем трекинг из Ostrov API
        $client = new ApiClient();
        $tracking = $client->getTracking($ostrovOrderId);

        $this->arResult['TRACKING'] = $tracking;
    }

    private function getOstrovOrderId(Order $order): string
    {
        $propertyCollection = $order->getPropertyCollection();
        $prop = $propertyCollection->getItemByOrderPropertyCode(self::ORDER_PROP_CODE);

        if (!$prop) {
            return '';
        }

        return (string)$prop->getValue();
    }
}
