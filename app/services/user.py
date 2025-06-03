from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.security import get_password_hash, verify_password

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get(self, user_id: int) -> Optional[models.User]:
        """Get a user by ID."""
        return crud.user.get(self.db, id=user_id)
    
    def get_by_email(self, email: str) -> Optional[models.User]:
        """Get a user by email."""
        return crud.user.get_by_email(self.db, email=email)
    
    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[models.User]:
        """Get multiple users with pagination."""
        return crud.user.get_multi(self.db, skip=skip, limit=limit)
    
    def create(self, user_in: schemas.UserCreate) -> models.User:
        """Create a new user."""
        # Check if user with email already exists
        if crud.user.get_by_email(self.db, email=user_in.email):
            raise ValueError("User with this email already exists")
        
        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        
        # Create user
        db_user = models.User(
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            is_superuser=user_in.is_superuser if hasattr(user_in, 'is_superuser') else False,
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(
        self, db_user: models.User, user_in: schemas.UserUpdate
    ) -> models.User:
        """Update a user."""
        user_data = user_in.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in user_data:
            hashed_password = get_password_hash(user_data["password"])
            del user_data["password"]
            user_data["hashed_password"] = hashed_password
        
        # Update user data
        for field, value in user_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def authenticate(self, email: str, password: str) -> Optional[models.User]:
        """Authenticate a user."""
        user = self.get_by_email(email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: models.User) -> bool:
        """Check if a user is active."""
        return user.is_active
    
    def is_superuser(self, user: models.User) -> bool:
        """Check if a user is a superuser."""
        return user.is_superuser
