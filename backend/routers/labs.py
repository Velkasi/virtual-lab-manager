from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid

from database import get_db
from models import Lab, VM, DeploymentLog
from schemas import LabCreate, LabResponse, DeploymentLogResponse
from services.deployment import deploy_lab

router = APIRouter()


@router.post("/labs", response_model=LabResponse)
async def create_lab(lab: LabCreate, db: Session = Depends(get_db)):
    """Crée un nouveau laboratoire virtuel."""
    # Vérifier que le nom du lab est unique
    existing_lab = db.query(Lab).filter(Lab.name == lab.name).first()
    if existing_lab:
        raise HTTPException(status_code=400, detail="Un lab avec ce nom existe déjà")
    
    # Créer le lab
    db_lab = Lab(
        name=lab.name,
        description=lab.description,
        status="created"
    )
    db.add(db_lab)
    db.flush()  # Pour obtenir l'ID du lab
    
    # Créer les VMs associées
    for vm_data in lab.vms:
        db_vm = VM(
            lab_id=db_lab.id,
            name=vm_data.name,
            vcpu=vm_data.vcpu,
            ram_mb=vm_data.ram_mb,
            disk_gb=vm_data.disk_gb,
            os_image=vm_data.os_image,
            ansible_config_yaml=lab.ansible_config_yaml,
            status="pending"
        )
        db.add(db_vm)
    
    db.commit()
    db.refresh(db_lab)
    return db_lab


@router.get("/labs", response_model=List[LabResponse])
async def list_labs(db: Session = Depends(get_db)):
    """Liste tous les laboratoires virtuels."""
    labs = db.query(Lab).all()
    return labs


@router.get("/labs/{lab_id}", response_model=LabResponse)
async def get_lab(lab_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère les détails d'un laboratoire spécifique."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouvé")
    return lab


@router.delete("/labs/{lab_id}")
async def delete_lab(lab_id: uuid.UUID, db: Session = Depends(get_db)):
    """Supprime un laboratoire virtuel."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouvé")
    
    # TODO: Implémenter la destruction de l'infrastructure Terraform
    
    db.delete(lab)
    db.commit()
    return {"message": "Lab supprimé avec succès"}


@router.post("/labs/{lab_id}/deploy")
async def deploy_lab_endpoint(
    lab_id: uuid.UUID, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Déclenche le déploiement d'un laboratoire virtuel."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouvé")
    
    if lab.status == "deploying":
        raise HTTPException(status_code=400, detail="Le lab est déjà en cours de déploiement")
    
    # Mettre à jour le statut
    lab.status = "deploying"
    db.commit()
    
    # Lancer le déploiement en arrière-plan
    background_tasks.add_task(deploy_lab, lab_id, db)
    
    return {"message": "Déploiement lancé"}


@router.get("/labs/{lab_id}/logs", response_model=List[DeploymentLogResponse])
async def get_lab_logs(lab_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère les logs de déploiement pour un laboratoire."""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab non trouvé")
    
    logs = db.query(DeploymentLog).filter(DeploymentLog.lab_id == lab_id).order_by(DeploymentLog.created_at).all()
    return logs

