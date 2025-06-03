# Import all models here so they can be discovered by SQLAlchemy
from .base import Base
from .user import User
from .trading import TradingStrategy, Backtest, BacktestExecution
from .chat import ChatRoom, ChatParticipant, ChatMessage

# This import must be after all models are imported
from .base import Base  # noqa

__all__ = [
    'Base',
    'User',
    'TradingStrategy',
    'Backtest',
    'BacktestExecution',
    'ChatRoom',
    'ChatParticipant',
    'ChatMessage',
]
