from pydantic import BaseModel, ConfigDict


class GameCreate(BaseModel):
    name: str
    price: int | None = None
    platform: str = ""
    usual_price: int | None = None
    best_price: int | None = None
    discount: int | None = None
    discount_price: int | None = None
    image: str | None = None
    url: str | None = None


class GameResponse(GameCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
