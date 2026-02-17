<?php

namespace Ostrov\Delivery\Service;

use Bitrix\Main\Config\Option;
use Bitrix\Main\Web\HttpClient;
use Ostrov\Delivery\Logger\Logger;

class ApiClient
{
    private const MODULE_ID = 'ostrov.delivery';

    private string $baseUrl;
    private string $apiKey;
    private int $timeout;

    public function __construct()
    {
        $this->baseUrl = rtrim((string)Option::get(self::MODULE_ID, 'api_base_url', ''), '/');
        $this->apiKey = (string)Option::get(self::MODULE_ID, 'api_key', '');
        $this->timeout = max(1, (int)Option::get(self::MODULE_ID, 'request_timeout', '10'));
    }

    public function calculateDelivery(array $payload): array
    {
        return $this->post('/api/v1/delivery/calculate', $payload);
    }

    public function createOrder(array $payload): array
    {
        return $this->post('/api/v1/orders', $payload);
    }

    public function getOrderStatus(string $orderId): array
    {
        return $this->get('/api/v1/orders/' . urlencode($orderId) . '/status');
    }

    private function post(string $path, array $payload): array
    {
        $client = $this->buildClient();
        $body = json_encode($payload, JSON_UNESCAPED_UNICODE);

        $result = $client->post($this->baseUrl . $path, $body ?: '{}');
        return $this->decodeResponse($client, $result, $path);
    }

    private function get(string $path): array
    {
        $client = $this->buildClient();
        $result = $client->get($this->baseUrl . $path);
        return $this->decodeResponse($client, $result, $path);
    }

    private function buildClient(): HttpClient
    {
        $client = new HttpClient(['socketTimeout' => $this->timeout, 'streamTimeout' => $this->timeout]);
        $client->setHeader('Content-Type', 'application/json', true);
        $client->setHeader('X-API-Key', $this->apiKey, true);

        return $client;
    }

    private function decodeResponse(HttpClient $client, string $response, string $path): array
    {
        $status = (int)$client->getStatus();

        if ($status < 200 || $status >= 300) {
            Logger::error('Ostrov API request failed', ['path' => $path, 'status' => $status, 'response' => $response]);
            throw new \RuntimeException('Ostrov API request failed with status ' . $status);
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            Logger::error('Ostrov API invalid JSON', ['path' => $path, 'status' => $status, 'response' => $response]);
            throw new \RuntimeException('Invalid API response');
        }

        return $data;
    }
}
