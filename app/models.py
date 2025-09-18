from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    services = relationship("Service", back_populates="application")


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    application = relationship("Application", back_populates="services")
    schemas = relationship("SchemaVersion", back_populates="service")


class SchemaVersion(Base):
    __tablename__ = "schema_versions"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    version = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    media_type = Column(String, nullable=False)  # json or yaml
    uploaded_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    service = relationship("Service", back_populates="schemas")
