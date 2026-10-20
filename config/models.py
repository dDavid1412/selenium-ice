from sqlalchemy import Column, Integer, String, Boolean
from config.database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    price = Column(Integer, index=True)
    platform = Column(String(100), index=True)
    usual_price = Column(Integer, index=True)
    best_price = Column(Integer, index=True)
    discount = Column(Integer, index=True)
    discount_price = Column(Boolean, default=False)
    image = Column(String(2048), index=True)
