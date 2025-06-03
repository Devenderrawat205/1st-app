from typing import Any

from sqlalchemy.ext.declarative import as_declaration, declared_attr

from app.models.base import Base as BaseModel

@as_declaration()
class Base(BaseModel):
    """Base class which provides automated table name and primary key column."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
