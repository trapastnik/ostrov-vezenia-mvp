<?php

namespace Ostrov\Delivery\Delivery;

use Bitrix\Main\Loader;
use Bitrix\Sale\Delivery\CalculationResult;
use Bitrix\Sale\Delivery\Services\Base;
use Bitrix\Sale\Shipment;
use Ostrov\Delivery\Logger\Logger;
use Ostrov\Delivery\Service\DeliveryCalculator;

/**
 * Bitrix delivery service handler for Ostrov Vezeniya.
 *
 * Integrates into checkout: calculates delivery cost via Ostrov API
 * (Pochta Rossii tariff + customs fee).
 */
class OstrovHandler extends Base
{
    protected static $isCalculatePriceImmediately = true;
    protected static $canHasProfiles = false;
    protected static $whetherAdminExtraServicesShow = false;

    public static function getClassTitle(): string
    {
        return 'Остров Везения';
    }

    public static function getClassDescription(): string
    {
        return 'Доставка через Почту России + таможенное оформление (Калининград → Россия)';
    }

    public function isCompatible(Shipment $shipment): bool
    {
        // Always show in checkout — calculateConcrete will handle missing ZIP gracefully
        return true;
    }

    protected function calculateConcrete(Shipment $shipment): CalculationResult
    {
        $result = new CalculationResult();

        try {
            $order = $shipment->getCollection()->getOrder();
            $props = $order->getPropertyCollection();

            // Get postal code
            $postalCode = $this->getPostalCode($props);
            if (!$postalCode) {
                $result->addError(new \Bitrix\Main\Error('Не указан почтовый индекс'));
                return $result;
            }

            // Calculate weight from shipment items
            $weightGrams = $this->getShipmentWeight($shipment);

            // Calculate total price from basket (in kopecks)
            $totalAmountKopecks = $this->getOrderTotalKopecks($order);

            // Call Ostrov API
            $calculator = new DeliveryCalculator();
            $apiResult = $calculator->calculate($postalCode, $weightGrams, $totalAmountKopecks);

            if (!($apiResult['available'] ?? false)) {
                $reason = $apiResult['rejection_reason'] ?? 'Доставка недоступна для указанного адреса';
                $result->addError(new \Bitrix\Main\Error($reason));
                return $result;
            }

            // total_cost_kopecks = delivery + customs, convert to rubles
            $deliveryPriceRub = ($apiResult['total_cost_kopecks'] ?? 0) / 100;
            $result->setDeliveryPrice(roundEx($deliveryPriceRub, 2));

            // Set delivery period
            $daysMin = $apiResult['delivery_days_min'] ?? 0;
            $daysMax = $apiResult['delivery_days_max'] ?? 0;
            if ($daysMax > 0) {
                $result->setPeriodDescription($daysMin . '-' . $daysMax . ' дн.');
            }

            // Store breakdown in description for transparency
            $deliveryRub = ($apiResult['delivery_cost_kopecks'] ?? 0) / 100;
            $customsRub = ($apiResult['customs_fee_kopecks'] ?? 0) / 100;
            $result->setDescription(
                sprintf('Почта России: %s ₽ + таможня: %s ₽', number_format($deliveryRub, 0, '.', ' '), number_format($customsRub, 0, '.', ' '))
            );

            Logger::info('Delivery calculated', [
                'postal_code' => $postalCode,
                'weight_g' => $weightGrams,
                'total_kopecks' => $totalAmountKopecks,
                'price_rub' => $deliveryPriceRub,
            ]);

        } catch (\Throwable $e) {
            Logger::error('Delivery calculation failed', [
                'error' => $e->getMessage(),
            ]);
            $result->addError(new \Bitrix\Main\Error('Ошибка расчёта доставки. Попробуйте позже.'));
        }

        return $result;
    }

    public function getConfigStructure(): array
    {
        return [
            'main' => [
                'TITLE' => 'Основные настройки',
                'DESCRIPTION' => 'Настройки задаются в параметрах модуля ostrov.delivery',
                'ITEMS' => [],
            ],
        ];
    }

    /**
     * Extract postal code from order properties.
     */
    private function getPostalCode($props): ?string
    {
        // Try standard ZIP property
        $zip = $this->findPropertyByCode($props, 'ZIP');
        if ($zip && !empty($zip->getValue())) {
            return trim($zip->getValue());
        }

        // Try via delivery location (some templates store ZIP there)
        $location = $props->getDeliveryLocation();
        if ($location) {
            $val = $location->getValue();
            if ($val && preg_match('/^\d{5,6}$/', trim($val))) {
                return trim($val);
            }
        }

        return null;
    }

    /**
     * Calculate total shipment weight in grams.
     */
    private function getShipmentWeight(Shipment $shipment): int
    {
        $weight = 0;

        foreach ($shipment->getShipmentItemCollection() as $shipmentItem) {
            $basketItem = $shipmentItem->getBasketItem();
            if (!$basketItem) {
                continue;
            }
            // Bitrix stores weight in grams by default
            $itemWeight = (int)$basketItem->getWeight();
            $quantity = (int)$shipmentItem->getQuantity();

            if ($itemWeight <= 0) {
                $itemWeight = 1000; // Default 1kg if not set
            }

            $weight += $itemWeight * $quantity;
        }

        return max($weight, 100); // Minimum 100g
    }

    /**
     * Get order total in kopecks.
     */
    private function getOrderTotalKopecks($order): int
    {
        $price = (float)$order->getPrice();
        return (int)round($price * 100);
    }

    /**
     * Find order property by CODE.
     */
    private function findPropertyByCode($props, string $code)
    {
        foreach ($props as $prop) {
            if ($prop->getField('CODE') === $code) {
                return $prop;
            }
        }
        return null;
    }
}
