from typing import Any, Generic, TypeVar, Optional
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

class BaseService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service class with common CRUD operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @abstractmethod
    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        pass
    
    @abstractmethod
    def get_multi(self, *, skip: int = 0, limit: int = 100, **filters) -> list[ModelType]:
        """Get multiple records with optional filtering and pagination."""
        pass
    
    @abstractmethod
    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        pass
    
    @abstractmethod
    def update(self, *, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update a record."""
        pass
    
    @abstractmethod
    def remove(self, *, id: Any) -> ModelType:
        """Delete a record."""
        pass
