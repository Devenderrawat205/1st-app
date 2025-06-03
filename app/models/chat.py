from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<ChatRoom {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="chat_participations")
    room = relationship("ChatRoom", back_populates="participants")
    
    def __repr__(self) -> str:
        return f"<ChatParticipant {self.user_id} in Room {self.room_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "is_admin": self.is_admin,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    reply_to_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    room = relationship("ChatRoom", back_populates="messages")
    reply_to = relationship("ChatMessage", remote_side=[id], backref="replies")
    
    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} by User {self.user_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "is_edited": self.is_edited,
            "user_id": self.user_id,
            "room_id": self.room_id,
            "reply_to_id": self.reply_to_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
