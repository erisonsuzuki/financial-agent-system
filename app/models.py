from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Enum as SQLAlchemyEnum,
    Numeric,
    Text,
    DateTime,
    JSON,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    REIT = "REIT"

class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("portfolio_id", "ticker", name="uq_assets_portfolio_ticker"),)
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    asset_type = Column(SQLAlchemyEnum(AssetType), nullable=False)
    sector = Column(String)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    portfolio = relationship("Portfolio", back_populates="assets")
    transactions = relationship("Transaction", back_populates="asset")
    dividends = relationship("Dividend", back_populates="asset")


class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="Default")

    user = relationship("User", back_populates="portfolios")
    assets = relationship("Asset", back_populates="portfolio")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    transaction_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="transactions")

class Dividend(Base):
    __tablename__ = "dividends"
    __table_args__ = (UniqueConstraint("asset_id", "payment_date", name="uq_dividends_asset_id_payment_date"),)
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    amount_per_share = Column(Numeric(10, 4), nullable=False)
    payment_date = Column(Date, nullable=False)
    asset = relationship("Asset", back_populates="dividends")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    actions = relationship("AgentAction", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")


class MagicLinkToken(Base):
    __tablename__ = "magic_link_tokens"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    purpose = Column(String, nullable=False, default="register")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    setup_used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AgentAction(Base):
    __tablename__ = "agent_actions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="actions")


class AssetPriceCache(Base):
    __tablename__ = "asset_price_cache"

    ticker = Column(String, primary_key=True)
    price = Column(Numeric(10, 2), nullable=False)
    source = Column(String, default="yfinance", nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)
