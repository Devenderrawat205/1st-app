from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)  # Store strategy code
    version = Column(String(20), default="1.0.0")
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), onupdate=datetime.utcnow)
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<TradingStrategy {self.name} v{self.version}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class Backtest(Base):
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    parameters = Column(Text)  # JSON string of backtest parameters
    results = Column(Text, nullable=True)  # JSON string of backtest results
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_balance = Column(Float, default=100000.0)
    final_balance = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), onupdate=datetime.utcnow)
    
    # Foreign Keys
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="backtests")
    owner = relationship("User", back_populates="backtests")
    executions = relationship("BacktestExecution", back_populates="backtest", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Backtest {self.name} ({self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_balance": self.initial_balance,
            "final_balance": self.final_balance,
            "strategy_id": self.strategy_id,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class BacktestExecution(Base):
    __tablename__ = "backtest_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    logs = Column(Text, nullable=True)  # Execution logs
    metrics = Column(Text, nullable=True)  # JSON string of execution metrics
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    backtest_id = Column(Integer, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    backtest = relationship("Backtest", back_populates="executions")
    
    def __repr__(self) -> str:
        return f"<BacktestExecution {self.id} ({self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "backtest_id": self.backtest_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
