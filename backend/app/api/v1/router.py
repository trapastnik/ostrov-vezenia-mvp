from fastapi import APIRouter

from app.api.v1.admin_batches import router as admin_batches_router
from app.api.v1.admin_company import router as admin_company_router
from app.api.v1.admin_customs import router as admin_customs_router
from app.api.v1.admin_groups import router as admin_groups_router
from app.api.v1.admin_health import router as admin_health_router
from app.api.v1.admin_version import router as admin_version_router
from app.api.v1.admin_orders import router as admin_orders_router
from app.api.v1.admin_pochta import router as admin_pochta_router
from app.api.v1.admin_shops import router as admin_shops_router
from app.api.v1.admin_tnved import router as admin_tnved_router
from app.api.v1.auth import router as auth_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.orders import router as orders_router
from app.api.v1.tracking import router as tracking_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(delivery_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(tracking_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(admin_orders_router)
api_v1_router.include_router(admin_batches_router)
api_v1_router.include_router(admin_shops_router)
api_v1_router.include_router(admin_pochta_router)
api_v1_router.include_router(admin_groups_router)
api_v1_router.include_router(admin_customs_router)
api_v1_router.include_router(admin_company_router)
api_v1_router.include_router(admin_tnved_router)
api_v1_router.include_router(admin_health_router)
api_v1_router.include_router(admin_version_router)
