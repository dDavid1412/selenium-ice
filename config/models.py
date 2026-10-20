from sqlalchemy import BigInteger, Column, Integer, String
from config.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    price = Column(Integer, nullable=True, index=True)
    platform = Column(String(100), nullable=False, default="", index=True)
    usual_price = Column(Integer, nullable=True, index=True)
    best_price = Column(Integer, nullable=True, index=True)
    discount = Column(Integer, nullable=True, index=True)
    discount_price = Column(Integer, nullable=True, index=True)
    image = Column(String(2048), nullable=True)
