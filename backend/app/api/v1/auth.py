from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.operator import Operator
from app.schemas.auth import LoginRequest, OperatorInfo, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Operator).where(Operator.email == body.email, Operator.is_active.is_(True)))
    operator = result.scalar_one_or_none()

    if not operator or not verify_password(body.password, operator.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(str(operator.id), operator.role)

    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        operator=OperatorInfo(id=str(operator.id), name=operator.name, role=operator.role),
    )
