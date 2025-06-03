from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.services.user import UserService

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Login a user and return an access token."""
        # Authenticate user
        user = self.user_service.authenticate(email, password)
        if not user:
            return None
        
        # Update last login time
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict()
        }
    
    def get_current_user(self, token: str) -> Optional[models.User]:
        """Get the current user from a JWT token."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            user_id: int = int(payload.get("sub"))
            if user_id is None:
                return None
        except (jwt.JWTError, ValueError):
            return None
        
        user = self.user_service.get(user_id)
        return user
    
    def refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Refresh an access token."""
        user = self.get_current_user(token)
        if not user:
            return None
        
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def register(self, user_in: schemas.UserCreate) -> models.User:
        """Register a new user."""
        return self.user_service.create(user_in)
