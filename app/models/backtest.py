from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from ..db.base import Base

class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Backtest configuration
    symbol = Column(String)  # e.g., "NIFTY", "RELIANCE"
    timeframe = Column(String)  # e.g., "1d", "1h", "15m"
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    initial_capital = Column(Float)
    
    # Results
    status = Column(String)  # "pending", "running", "completed", "failed"
    results = Column(JSON)  # Store backtest results
    metrics = Column(JSON)  # Performance metrics
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="backtests")
    owner = relationship("User", back_populates="backtests")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room = Column(String, index=True)  # Could be "general" or "strategy-{id}"
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
