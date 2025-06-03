from sqlalchemy.ext.declarative import as_declaration, declared_attr

@as_declaration()
class Base:
    """Base class which provides automated table name and primary key column."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    def dict(self):
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
