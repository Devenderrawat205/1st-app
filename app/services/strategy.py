from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.crud import strategy as crud_strategy
from app.services.base import BaseService

class StrategyService(BaseService):
    """Service for trading strategy operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.crud = crud_strategy
    
    def create(
        self, *, obj_in: schemas.StrategyCreate, owner_id: int
    ) -> models.TradingStrategy:
        """Create a new trading strategy."""
        # Check if strategy with same name and version already exists for this user
        existing = self.crud.get_by_name_and_version(
            self.db, name=obj_in.name, version=obj_in.version, owner_id=owner_id
        )
        if existing:
            raise ValueError("Strategy with this name and version already exists")
        
        return self.crud.create_with_owner(
            self.db, obj_in=obj_in, owner_id=owner_id
        )
    
    def update(
        self, *, db_obj: models.TradingStrategy, obj_in: schemas.StrategyUpdate
    ) -> models.TradingStrategy:
        """Update a trading strategy."""
        # Check if updating to a new name/version that already exists
        if (hasattr(obj_in, 'name') and hasattr(obj_in, 'version')) and \
           (obj_in.name != db_obj.name or obj_in.version != db_obj.version):
            existing = self.crud.get_by_name_and_version(
                self.db, 
                name=obj_in.name, 
                version=obj_in.version, 
                owner_id=db_obj.owner_id
            )
            if existing and existing.id != db_obj.id:
                raise ValueError("Strategy with this name and version already exists")
        
        return self.crud.update(self.db, db_obj=db_obj, obj_in=obj_in)
    
    def get(self, id: int) -> Optional[models.TradingStrategy]:
        """Get a strategy by ID."""
        return self.crud.get(self.db, id=id)
    
    def get_by_name_and_version(
        self, name: str, version: str, owner_id: int
    ) -> Optional[models.TradingStrategy]:
        """Get a strategy by name and version."""
        return self.crud.get_by_name_and_version(
            self.db, name=name, version=version, owner_id=owner_id
        )
    
    def get_multi(
        self, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[models.TradingStrategy]:
        """Get multiple strategies with optional filtering."""
        return self.crud.get_multi(
            self.db, skip=skip, limit=limit, **filters
        )
    
    def get_multi_by_owner(
        self, *, owner_id: int, skip: int = 0, limit: int = 100, **filters
    ) -> List[models.TradingStrategy]:
        """Get multiple strategies for a specific owner."""
        return self.crud.get_multi_by_owner(
            self.db, owner_id=owner_id, skip=skip, limit=limit, **filters
        )
    
    def get_public_strategies(
        self, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[models.TradingStrategy]:
        """Get public trading strategies."""
        return self.crud.get_public_strategies(
            self.db, skip=skip, limit=limit, **filters
        )
    
    def remove(self, *, id: int) -> models.TradingStrategy:
        """Delete a strategy."""
        # TODO: Add checks for associated backtests before deletion
        return self.crud.remove(self.db, id=id)
    
    def validate_strategy_code(self, code: str) -> Dict[str, Any]:
        """Validate strategy code syntax and structure."""
        # TODO: Implement actual validation logic
        # This would typically check that the code:
        # 1. Has the required functions (e.g., initialize, handle_data)
        # 2. Has valid syntax
        # 3. Doesn't use disallowed modules/functions
        # 4. Meets other requirements
        
        # For now, just return a mock validation result
        return {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
