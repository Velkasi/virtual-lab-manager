from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class VMCreate(BaseModel):
    name: str
    vcpu: int = Field(ge=1, le=16)
    ram_mb: int = Field(ge=512, le=32768)
    disk_gb: int = Field(ge=10, le=500)
    os_image: str


class VMResponse(BaseModel):
    id: uuid.UUID
    lab_id: uuid.UUID
    name: str
    vcpu: int
    ram_mb: int
    disk_gb: int
    os_image: str
    ssh_port: Optional[int]
    vnc_port: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LabCreate(BaseModel):
    name: str
    description: Optional[str] = None
    vms: List[VMCreate]
    ansible_config_yaml: Optional[str] = None


class LabResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    vms: List[VMResponse] = []

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


class DeploymentLogResponse(BaseModel):
    id: uuid.UUID
    lab_id: uuid.UUID
    log_type: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SSHConnectionInfo(BaseModel):
    host: str
    port: int
    username: str = "ubuntu"


class VNCConnectionInfo(BaseModel):
    host: str
    port: int

