from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import uuid


# Table de liaison pour les tags des labs
lab_tags = Table(
    'lab_tags',
    Base.metadata,
    Column('lab_id', UUID(as_uuid=True), ForeignKey('labs.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True)
)


class Lab(Base):
    __tablename__ = "labs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    status = Column(String, default="created")  # created, deploying, deployed, error, deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    vms = relationship("VM", back_populates="lab", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=lab_tags, back_populates="labs")


class VM(Base):
    __tablename__ = "vms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False)
    name = Column(String, nullable=False)
    vcpu = Column(Integer, nullable=False)
    ram_mb = Column(Integer, nullable=False)
    disk_gb = Column(Integer, nullable=False)
    os_image = Column(String, nullable=False)
    ssh_port = Column(Integer, unique=True)
    vnc_port = Column(Integer, unique=True)
    status = Column(String, default="pending")  # pending, running, stopped, error
    ansible_config_yaml = Column(Text)
    terraform_state = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    lab = relationship("Lab", back_populates="vms")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    # Relations
    labs = relationship("Lab", secondary=lab_tags, back_populates="tags")


class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False)
    log_type = Column(String, nullable=False)  # terraform, ansible
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    lab = relationship("Lab")

