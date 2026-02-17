from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.operator import Operator
from app.models.shop import Shop


async def get_current_operator(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Operator:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    token = authorization[7:]
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    operator_id = payload.get("sub")
    if not operator_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(Operator).where(Operator.id == UUID(operator_id), Operator.is_active.is_(True)))
    operator = result.scalar_one_or_none()
    if not operator:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Operator not found")
    return operator


async def require_admin(operator: Operator = Depends(get_current_operator)) -> Operator:
    if operator.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return operator


async def verify_api_key(
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Shop:
    result = await db.execute(select(Shop).where(Shop.api_key == x_api_key, Shop.is_active.is_(True)))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return shop
