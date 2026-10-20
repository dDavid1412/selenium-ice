from pydantic import BaseModel, ConfigDict


class GameCreate(BaseModel):
    name: str
    price: int
    platform: str
    mean_price: int
    mode_price: int
    discount_price: bool = False
    image_url: str


class GameResponse(GameCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
