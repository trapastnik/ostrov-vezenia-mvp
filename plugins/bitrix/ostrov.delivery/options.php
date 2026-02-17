<?php

use Bitrix\Main\Config\Option;

$moduleId = 'ostrov.delivery';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && check_bitrix_sessid()) {
    Option::set($moduleId, 'api_base_url', trim((string)($_POST['api_base_url'] ?? '')));
    Option::set($moduleId, 'api_key', trim((string)($_POST['api_key'] ?? '')));
    Option::set($moduleId, 'request_timeout', trim((string)($_POST['request_timeout'] ?? '10')));
}

$apiBaseUrl = Option::get($moduleId, 'api_base_url', 'http://localhost:8000');
$apiKey = Option::get($moduleId, 'api_key', '');
$requestTimeout = Option::get($moduleId, 'request_timeout', '10');
?>
<form method="post" action="<?= $APPLICATION->GetCurPage() ?>?mid=<?= htmlspecialcharsbx($moduleId) ?>&lang=<?= LANGUAGE_ID ?>">
    <?= bitrix_sessid_post() ?>
    <table class="adm-detail-content-table edit-table">
        <tr>
            <td width="40%">API Base URL</td>
            <td width="60%"><input type="text" name="api_base_url" value="<?= htmlspecialcharsbx($apiBaseUrl) ?>" size="60"></td>
        </tr>
        <tr>
            <td>X-API-Key</td>
            <td><input type="text" name="api_key" value="<?= htmlspecialcharsbx($apiKey) ?>" size="60"></td>
        </tr>
        <tr>
            <td>Timeout (seconds)</td>
            <td><input type="number" name="request_timeout" min="1" max="60" value="<?= htmlspecialcharsbx($requestTimeout) ?>"></td>
        </tr>
    </table>
    <input type="submit" name="save" value="Save" class="adm-btn-save">
</form>
