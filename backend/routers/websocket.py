from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import VM
from services.websocket_service import websocket_proxy_service
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/ssh/{vm_id}")
async def websocket_ssh_endpoint(websocket: WebSocket, vm_id: str, db: Session = Depends(get_db)):
    """Endpoint WebSocket pour les connexions SSH."""
    await websocket.accept()
    
    try:
        # Vérifier que la VM existe et récupérer ses informations
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            await websocket.send_text("Erreur: VM non trouvée")
            await websocket.close()
            return
        
        if not vm.ssh_port:
            await websocket.send_text("Erreur: Port SSH non configuré pour cette VM")
            await websocket.close()
            return
        
        if vm.status != "running":
            await websocket.send_text("Erreur: La VM n'est pas en cours d'exécution")
            await websocket.close()
            return
        
        # Établir la connexion SSH via le proxy
        await websocket_proxy_service.handle_ssh_connection(
            websocket, vm_id, "localhost", vm.ssh_port
        )
        
    except WebSocketDisconnect:
        logger.info(f"Connexion SSH WebSocket fermée pour VM {vm_id}")
    except Exception as e:
        logger.error(f"Erreur dans la connexion SSH WebSocket pour VM {vm_id}: {e}")
        try:
            await websocket.send_text(f"Erreur: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.websocket("/ws/vnc/{vm_id}")
async def websocket_vnc_endpoint(websocket: WebSocket, vm_id: str, db: Session = Depends(get_db)):
    """Endpoint WebSocket pour les connexions VNC."""
    await websocket.accept()
    
    try:
        # Vérifier que la VM existe et récupérer ses informations
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            await websocket.send_text("Erreur: VM non trouvée")
            await websocket.close()
            return
        
        if not vm.vnc_port:
            await websocket.send_text("Erreur: Port VNC non configuré pour cette VM")
            await websocket.close()
            return
        
        if vm.status != "running":
            await websocket.send_text("Erreur: La VM n'est pas en cours d'exécution")
            await websocket.close()
            return
        
        # Établir la connexion VNC via le proxy
        await websocket_proxy_service.handle_vnc_connection(
            websocket, vm_id, "localhost", vm.vnc_port
        )
        
    except WebSocketDisconnect:
        logger.info(f"Connexion VNC WebSocket fermée pour VM {vm_id}")
    except Exception as e:
        logger.error(f"Erreur dans la connexion VNC WebSocket pour VM {vm_id}: {e}")
        try:
            await websocket.send_text(f"Erreur: {str(e)}")
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get("/connections/{vm_id}")
async def get_vm_connections(vm_id: str):
    """Récupère les connexions actives pour une VM."""
    connections = websocket_proxy_service.get_active_connections_for_vm(vm_id)
    return {
        "vm_id": vm_id,
        "active_connections": len(connections),
        "connections": [
            {
                "type": conn["type"],
                "connection_time": "N/A"  # Pourrait être ajouté plus tard
            }
            for conn in connections
        ]
    }

