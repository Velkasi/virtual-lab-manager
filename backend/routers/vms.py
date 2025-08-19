from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from database import get_db
from models import VM
from schemas import VMResponse, SSHConnectionInfo, VNCConnectionInfo
from services.vm_management import start_vm, stop_vm, restart_vm

router = APIRouter()


@router.get("/vms", response_model=List[VMResponse])
async def list_vms(
    lab_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """Liste toutes les machines virtuelles (peut être filtré par lab_id)."""
    query = db.query(VM)
    if lab_id:
        query = query.filter(VM.lab_id == lab_id)
    vms = query.all()
    return vms


@router.get("/vms/{vm_id}", response_model=VMResponse)
async def get_vm(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère les détails d'une machine virtuelle spécifique."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    return vm


@router.post("/vms/{vm_id}/start")
async def start_vm_endpoint(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Démarre une machine virtuelle."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    
    try:
        success = await start_vm(vm)
        if success:
            vm.status = "running"
            db.commit()
            return {"message": "VM démarrée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Échec du démarrage de la VM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du démarrage: {str(e)}")


@router.post("/vms/{vm_id}/stop")
async def stop_vm_endpoint(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Arrête une machine virtuelle."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    
    try:
        success = await stop_vm(vm)
        if success:
            vm.status = "stopped"
            db.commit()
            return {"message": "VM arrêtée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Échec de l'arrêt de la VM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'arrêt: {str(e)}")


@router.post("/vms/{vm_id}/restart")
async def restart_vm_endpoint(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Redémarre une machine virtuelle."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    
    try:
        success = await restart_vm(vm)
        if success:
            vm.status = "running"
            db.commit()
            return {"message": "VM redémarrée avec succès"}
        else:
            raise HTTPException(status_code=500, detail="Échec du redémarrage de la VM")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du redémarrage: {str(e)}")


@router.get("/vms/{vm_id}/ssh_access", response_model=SSHConnectionInfo)
async def get_ssh_access(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère les informations de connexion SSH pour une VM."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    
    if not vm.ssh_port:
        raise HTTPException(status_code=400, detail="Port SSH non configuré pour cette VM")
    
    return SSHConnectionInfo(
        host="localhost",  # Ou l'IP du serveur hôte
        port=vm.ssh_port
    )


@router.get("/vms/{vm_id}/vnc_access", response_model=VNCConnectionInfo)
async def get_vnc_access(vm_id: uuid.UUID, db: Session = Depends(get_db)):
    """Récupère les informations de connexion VNC pour une VM."""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM non trouvée")
    
    if not vm.vnc_port:
        raise HTTPException(status_code=400, detail="Port VNC non configuré pour cette VM")
    
    return VNCConnectionInfo(
        host="localhost",  # Ou l'IP du serveur hôte
        port=vm.vnc_port
    )

