from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class OperatorInfo(BaseModel):
    id: str
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    operator: OperatorInfo
