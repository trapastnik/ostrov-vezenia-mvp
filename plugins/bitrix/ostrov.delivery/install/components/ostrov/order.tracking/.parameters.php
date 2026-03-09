<?php

if (!defined('B_PROLOG_INCLUDED') || B_PROLOG_INCLUDED !== true) {
    die();
}

$arComponentParameters = [
    'PARAMETERS' => [
        'ORDER_ID' => [
            'PARENT' => 'BASE',
            'NAME' => 'ID заказа в Битрикс',
            'TYPE' => 'STRING',
            'DEFAULT' => '',
        ],
    ],
];
