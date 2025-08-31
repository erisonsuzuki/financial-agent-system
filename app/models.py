from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    REIT = "REIT"

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(SQLAlchemyEnum(AssetType), nullable=False)
    sector = Column(String)
    transactions = relationship("Transaction", back_populates="asset")
    dividends = relationship("Dividend", back_populates="asset")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    transaction_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="transactions")

class Dividend(Base):
    __tablename__ = "dividends"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    amount_per_share = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="dividends")
