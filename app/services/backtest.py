from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.crud import backtest as crud_backtest
from app.services.base import BaseService

class BacktestService(BaseService):
    """Service for backtest operations."""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.crud = crud_backtest
    
    def create(
        self, *, obj_in: schemas.BacktestCreate, owner_id: int
    ) -> models.Backtest:
        """Create a new backtest."""
        db_obj = self.crud.create_with_owner(
            self.db, obj_in=obj_in, owner_id=owner_id
        )
        return db_obj
    
    def update(
        self, *, db_obj: models.Backtest, obj_in: schemas.BacktestUpdate
    ) -> models.Backtest:
        """Update a backtest."""
        return self.crud.update(self.db, db_obj=db_obj, obj_in=obj_in)
    
    def get(self, id: int) -> Optional[models.Backtest]:
        """Get a backtest by ID."""
        return self.crud.get(self.db, id=id)
    
    def get_multi(
        self, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[models.Backtest]:
        """Get multiple backtests with optional filtering."""
        return self.crud.get_multi(
            self.db, skip=skip, limit=limit, **filters
        )
    
    def get_multi_by_owner(
        self, *, owner_id: int, skip: int = 0, limit: int = 100, **filters
    ) -> List[models.Backtest]:
        """Get multiple backtests for a specific owner."""
        return self.crud.get_multi_by_owner(
            self.db, owner_id=owner_id, skip=skip, limit=limit, **filters
        )
    
    def remove(self, *, id: int) -> models.Backtest:
        """Delete a backtest."""
        return self.crud.remove(self.db, id=id)
    
    def start_execution(
        self, *, backtest_id: int, user_id: int
    ) -> models.BacktestExecution:
        """Start a backtest execution."""
        # Get the backtest
        backtest = self.get(backtest_id)
        if not backtest:
            raise ValueError("Backtest not found")
        
        # Check ownership
        if backtest.owner_id != user_id:
            raise ValueError("Not authorized to execute this backtest")
        
        # Create execution record
        execution_in = schemas.BacktestExecutionCreate(
            backtest_id=backtest_id,
            status="pending"
        )
        
        db_execution = crud_backtest.execution.create(
            self.db, obj_in=execution_in
        )
        
        # TODO: Add actual backtest execution logic here
        # This would typically be handled by a background task/worker
        
        return db_execution
    
    def get_execution(
        self, execution_id: int, user_id: int
    ) -> Optional[models.BacktestExecution]:
        """Get a backtest execution by ID with ownership check."""
        execution = crud_backtest.execution.get(self.db, id=execution_id)
        if not execution:
            return None
            
        # Verify ownership
        if execution.backtest.owner_id != user_id:
            return None
            
        return execution
    
    def get_executions(
        self, backtest_id: int, user_id: int, **filters
    ) -> List[models.BacktestExecution]:
        """Get all executions for a backtest with ownership check."""
        backtest = self.get(backtest_id)
        if not backtest or backtest.owner_id != user_id:
            return []
            
        return crud_backtest.execution.get_multi_by_backtest(
            self.db, backtest_id=backtest_id, **filters
        )
