from pydantic import BaseModel


class TnVedSearchResult(BaseModel):
    code: str
    name: str
    level: int
    unit: str | None = None

    model_config = {"from_attributes": True}


class TnVedSearchResponse(BaseModel):
    items: list[TnVedSearchResult]
    total: int


class TnVedDetailResponse(BaseModel):
    code: str
    name: str
    level: int
    unit: str | None = None
    note: str | None = None
    parent_code: str | None = None
    # Иерархия: цепочка от корневой группы до текущего кода
    hierarchy: list[TnVedSearchResult] = []

    model_config = {"from_attributes": True}
