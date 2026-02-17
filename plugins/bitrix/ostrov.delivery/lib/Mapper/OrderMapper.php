<?php

namespace Ostrov\Delivery\Mapper;

use Bitrix\Sale\Order;

class OrderMapper
{
    public static function toOstrovPayload(Order $order): array
    {
        $propertyCollection = $order->getPropertyCollection();

        $recipientName = (string)($propertyCollection->getPayerName()?->getValue() ?? '');
        $recipientPhone = (string)($propertyCollection->getPhone()?->getValue() ?? '');
        $recipientEmail = (string)($order->getField('USER_EMAIL') ?? '');
        $recipientAddress = (string)($propertyCollection->getAddress()?->getValue() ?? '');
        $postalCode = (string)(self::findProperty($propertyCollection, ['ZIP', 'POSTAL_CODE', 'INDEX']) ?? '');

        $items = [];
        $totalAmountKopecks = 0;
        $totalWeightGrams = 0;

        /** @var \Bitrix\Sale\BasketItem $basketItem */
        foreach ($order->getBasket() as $basketItem) {
            $name = (string)$basketItem->getField('NAME');
            $quantity = (int)$basketItem->getQuantity();
            $priceKopecks = (int)round((float)$basketItem->getPrice() * 100);
            $weightGrams = (int)$basketItem->getField('WEIGHT');

            if ($weightGrams <= 0) {
                $weightGrams = 1000;
            }

            $items[] = [
                'name' => $name,
                'quantity' => $quantity,
                'price_kopecks' => $priceKopecks,
                'weight_grams' => $weightGrams,
            ];

            $totalAmountKopecks += $priceKopecks * $quantity;
            $totalWeightGrams += $weightGrams * $quantity;
        }

        return [
            'external_order_id' => (string)$order->getField('ACCOUNT_NUMBER'),
            'recipient' => [
                'name' => $recipientName,
                'phone' => $recipientPhone,
                'email' => $recipientEmail ?: null,
                'address' => $recipientAddress,
                'postal_code' => $postalCode,
            ],
            'items' => $items,
            '_meta' => [
                'total_amount_kopecks' => $totalAmountKopecks,
                'total_weight_grams' => $totalWeightGrams,
            ],
        ];
    }

    private static function findProperty($propertyCollection, array $codes): ?string
    {
        foreach ($codes as $code) {
            $prop = $propertyCollection->getItemByOrderPropertyCode($code);
            if ($prop && (string)$prop->getValue() !== '') {
                return (string)$prop->getValue();
            }
        }

        return null;
    }
}
