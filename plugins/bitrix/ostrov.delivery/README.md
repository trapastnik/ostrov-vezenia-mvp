# ostrov.delivery (Bitrix module skeleton)

This folder contains a standalone module skeleton for integrating Ostrov delivery API with Bitrix store.

## Important: cloud compatibility

- If your store is **Bitrix24 cloud (SaaS)**, custom PHP modules cannot be installed.
- If your store is **1C-Bitrix hosted in cloud/VPS** with file access (`/bitrix/modules`), this module is installable.

## Current scope

- Delivery calculation client (`/api/v1/delivery/calculate`)
- Order export client (`/api/v1/orders`)
- Basic order mapping from Bitrix order entities
- Event hook scaffold for order save
- Admin options page scaffold

## Next step

Wire this folder into a real Bitrix instance under:

`/bitrix/modules/ostrov.delivery`

and register handlers on install.
