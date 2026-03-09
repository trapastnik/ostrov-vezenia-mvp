<?php

if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) {
    die();
}

/**
 * @var array $arResult
 *   TRACKING — данные трекинга из API
 *   ERROR — текст ошибки
 */

$tracking = $arResult['TRACKING'] ?? null;
$error = $arResult['ERROR'] ?? '';

$statusLabels = [
    'accepted' => 'Принят',
    'awaiting_pickup' => 'Ожидает забора',
    'received_warehouse' => 'На складе',
    'batch_forming' => 'Формирование партии',
    'customs_presented' => 'Таможенное оформление',
    'customs_cleared' => 'Таможня пройдена',
    'awaiting_carrier' => 'Подготовка к отправке',
    'shipped' => 'Отправлен',
    'in_transit' => 'В пути',
    'delivered' => 'Доставлен',
    'cancelled' => 'Отменён',
    'problem' => 'Проблема',
];

$statusColors = [
    'accepted' => '#3b82f6',
    'awaiting_pickup' => '#eab308',
    'received_warehouse' => '#6366f1',
    'batch_forming' => '#a855f7',
    'customs_presented' => '#f97316',
    'customs_cleared' => '#14b8a6',
    'awaiting_carrier' => '#06b6d4',
    'shipped' => '#0ea5e9',
    'in_transit' => '#f59e0b',
    'delivered' => '#22c55e',
    'cancelled' => '#6b7280',
    'problem' => '#ef4444',
];
?>

<div class="ostrov-tracking">
    <?php if ($error): ?>
        <div class="ostrov-tracking__error">
            <?= htmlspecialcharsbx($error) ?>
        </div>
    <?php elseif ($tracking): ?>
        <?php
            $status = $tracking['status'] ?? '';
            $statusLabel = $statusLabels[$status] ?? $status;
            $statusColor = $statusColors[$status] ?? '#6b7280';
        ?>

        <!-- Status header -->
        <div class="ostrov-tracking__header">
            <div class="ostrov-tracking__title">Статус доставки</div>
            <div class="ostrov-tracking__status" style="color: <?= $statusColor ?>">
                <?= htmlspecialcharsbx($statusLabel) ?>
            </div>
        </div>

        <!-- Track numbers -->
        <?php if (!empty($tracking['track_number'])): ?>
            <div class="ostrov-tracking__track">
                <span class="ostrov-tracking__track-label">Трек-номер Почты России:</span>
                <strong><?= htmlspecialcharsbx($tracking['track_number']) ?></strong>
            </div>
        <?php endif; ?>

        <!-- Events timeline -->
        <?php $events = array_reverse($tracking['events'] ?? []); ?>
        <?php if (!empty($events)): ?>
            <div class="ostrov-tracking__timeline">
                <?php foreach ($events as $i => $event): ?>
                    <?php
                        $isFirst = ($i === 0);
                        $date = '';
                        if (!empty($event['created_at'])) {
                            $ts = strtotime($event['created_at']);
                            if ($ts) {
                                $date = date('d.m.Y H:i', $ts);
                            }
                        }
                    ?>
                    <div class="ostrov-tracking__event <?= $isFirst ? 'ostrov-tracking__event--active' : '' ?>">
                        <div class="ostrov-tracking__event-dot"></div>
                        <div class="ostrov-tracking__event-content">
                            <div class="ostrov-tracking__event-text">
                                <?= htmlspecialcharsbx($event['description'] ?? '') ?>
                            </div>
                            <?php if ($date): ?>
                                <div class="ostrov-tracking__event-date"><?= $date ?></div>
                            <?php endif; ?>
                            <?php if (!empty($event['location'])): ?>
                                <div class="ostrov-tracking__event-location">
                                    <?= htmlspecialcharsbx($event['location']) ?>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php else: ?>
            <div class="ostrov-tracking__empty">Нет событий</div>
        <?php endif; ?>
    <?php endif; ?>
</div>

<style>
.ostrov-tracking {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 500px;
    margin: 16px 0;
}
.ostrov-tracking__error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: #dc2626;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 14px;
}
.ostrov-tracking__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e7eb;
}
.ostrov-tracking__title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
}
.ostrov-tracking__status {
    font-size: 15px;
    font-weight: 600;
}
.ostrov-tracking__track {
    margin-bottom: 16px;
    font-size: 14px;
    color: #4b5563;
}
.ostrov-tracking__track-label {
    margin-right: 4px;
}
.ostrov-tracking__timeline {
    position: relative;
    padding-left: 24px;
}
.ostrov-tracking__timeline::before {
    content: '';
    position: absolute;
    left: 7px;
    top: 4px;
    bottom: 4px;
    width: 2px;
    background: #e5e7eb;
}
.ostrov-tracking__event {
    position: relative;
    padding-bottom: 16px;
}
.ostrov-tracking__event:last-child {
    padding-bottom: 0;
}
.ostrov-tracking__event-dot {
    position: absolute;
    left: -20px;
    top: 4px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #d1d5db;
    border: 2px solid #fff;
    z-index: 1;
}
.ostrov-tracking__event--active .ostrov-tracking__event-dot {
    background: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}
.ostrov-tracking__event-text {
    font-size: 14px;
    color: #1f2937;
    font-weight: 500;
}
.ostrov-tracking__event--active .ostrov-tracking__event-text {
    color: #1d4ed8;
}
.ostrov-tracking__event-date {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 2px;
}
.ostrov-tracking__event-location {
    font-size: 13px;
    color: #6b7280;
    margin-top: 2px;
}
.ostrov-tracking__empty {
    color: #9ca3af;
    font-size: 14px;
    text-align: center;
    padding: 16px 0;
}
</style>
