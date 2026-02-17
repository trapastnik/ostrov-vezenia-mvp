from pydantic import BaseModel


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
