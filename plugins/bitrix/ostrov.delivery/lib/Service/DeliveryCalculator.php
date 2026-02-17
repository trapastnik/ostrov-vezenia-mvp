<?php

namespace Ostrov\Delivery\Service;

class DeliveryCalculator
{
    public function calculate(string $postalCode, int $weightGrams, int $totalAmountKopecks): array
    {
        $client = new ApiClient();

        return $client->calculateDelivery([
            'postal_code' => $postalCode,
            'weight_grams' => $weightGrams,
            'total_amount_kopecks' => $totalAmountKopecks,
        ]);
    }
}
