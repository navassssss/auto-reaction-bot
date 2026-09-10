from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuthorizedChannel(Base):
    __tablename__ = "authorized_channels"
    id = Column(Integer, primary_key=True, index=True)
    telegram_chat_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    title = Column(String(255))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ReactionBot(Base):
    __tablename__ = "reaction_bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    telegram_bot_id = Column(BigInteger, unique=True, nullable=False)
    token_encrypted = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_success_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    
    tasks = relationship("ReactionTask", back_populates="bot", cascade="all, delete-orphan")

class ReactionJob(Base):
    __tablename__ = "reaction_jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    telegram_chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    post_url = Column(Text, nullable=False)
    emoji = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="queued", index=True) # queued, running, completed, partially_completed, failed, cancelled
    total_tasks = Column(Integer, default=0)
    successful_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    pending_tasks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    tasks = relationship("ReactionTask", back_populates="job", cascade="all, delete-orphan")

class ReactionTask(Base):
    __tablename__ = "reaction_tasks"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), ForeignKey("reaction_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    bot_id = Column(BigInteger, ForeignKey("reaction_bots.telegram_bot_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="pending", index=True) # pending, running, success, failed, cancelled
    attempts = Column(Integer, default=0)
    error_code = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    job = relationship("ReactionJob", back_populates="tasks")
    bot = relationship("ReactionBot", back_populates="tasks")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    admin_telegram_id = Column(BigInteger, nullable=False)
    action = Column(String(100), nullable=False)
    job_id = Column(String(100))
    target_chat_id = Column(BigInteger)
    target_message_id = Column(BigInteger)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_ = Column("metadata", JSONB)

class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
