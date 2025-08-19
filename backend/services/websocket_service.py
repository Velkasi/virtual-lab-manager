import asyncio
import websockets
import socket
import threading
from typing import Dict, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class WebSocketProxyService:
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}
    
    async def handle_ssh_connection(self, websocket, vm_id: str, ssh_host: str, ssh_port: int):
        """Gère une connexion SSH via WebSocket."""
        connection_id = str(uuid.uuid4())
        
        try:
            # Établir la connexion SSH
            ssh_reader, ssh_writer = await asyncio.open_connection(ssh_host, ssh_port)
            
            # Stocker la connexion
            self.active_connections[connection_id] = {
                'type': 'ssh',
                'vm_id': vm_id,
                'websocket': websocket,
                'ssh_reader': ssh_reader,
                'ssh_writer': ssh_writer
            }
            
            # Créer les tâches pour transférer les données
            tasks = [
                asyncio.create_task(self._websocket_to_ssh(websocket, ssh_writer, connection_id)),
                asyncio.create_task(self._ssh_to_websocket(ssh_reader, websocket, connection_id))
            ]
            
            # Attendre qu'une des tâches se termine
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Annuler les tâches restantes
            for task in pending:
                task.cancel()
            
        except Exception as e:
            logger.error(f"Erreur dans la connexion SSH {connection_id}: {e}")
            await websocket.send(f"Erreur de connexion SSH: {str(e)}")
        
        finally:
            # Nettoyer la connexion
            await self._cleanup_connection(connection_id)
    
    async def handle_vnc_connection(self, websocket, vm_id: str, vnc_host: str, vnc_port: int):
        """Gère une connexion VNC via WebSocket."""
        connection_id = str(uuid.uuid4())
        
        try:
            # Établir la connexion VNC
            vnc_reader, vnc_writer = await asyncio.open_connection(vnc_host, vnc_port)
            
            # Stocker la connexion
            self.active_connections[connection_id] = {
                'type': 'vnc',
                'vm_id': vm_id,
                'websocket': websocket,
                'vnc_reader': vnc_reader,
                'vnc_writer': vnc_writer
            }
            
            # Créer les tâches pour transférer les données
            tasks = [
                asyncio.create_task(self._websocket_to_vnc(websocket, vnc_writer, connection_id)),
                asyncio.create_task(self._vnc_to_websocket(vnc_reader, websocket, connection_id))
            ]
            
            # Attendre qu'une des tâches se termine
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Annuler les tâches restantes
            for task in pending:
                task.cancel()
        
        except Exception as e:
            logger.error(f"Erreur dans la connexion VNC {connection_id}: {e}")
            await websocket.send(f"Erreur de connexion VNC: {str(e)}")
        
        finally:
            # Nettoyer la connexion
            await self._cleanup_connection(connection_id)
    
    async def _websocket_to_ssh(self, websocket, ssh_writer, connection_id: str):
        """Transfère les données du WebSocket vers SSH."""
        try:
            async for message in websocket:
                if isinstance(message, str):
                    # Commande ou données texte
                    ssh_writer.write(message.encode('utf-8'))
                else:
                    # Données binaires
                    ssh_writer.write(message)
                await ssh_writer.drain()
        except Exception as e:
            logger.error(f"Erreur WebSocket->SSH {connection_id}: {e}")
    
    async def _ssh_to_websocket(self, ssh_reader, websocket, connection_id: str):
        """Transfère les données de SSH vers le WebSocket."""
        try:
            while True:
                data = await ssh_reader.read(1024)
                if not data:
                    break
                await websocket.send(data.decode('utf-8', errors='ignore'))
        except Exception as e:
            logger.error(f"Erreur SSH->WebSocket {connection_id}: {e}")
    
    async def _websocket_to_vnc(self, websocket, vnc_writer, connection_id: str):
        """Transfère les données du WebSocket vers VNC."""
        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    vnc_writer.write(message)
                else:
                    # Convertir les messages texte en bytes pour VNC
                    vnc_writer.write(message.encode('utf-8'))
                await vnc_writer.drain()
        except Exception as e:
            logger.error(f"Erreur WebSocket->VNC {connection_id}: {e}")
    
    async def _vnc_to_websocket(self, vnc_reader, websocket, connection_id: str):
        """Transfère les données de VNC vers le WebSocket."""
        try:
            while True:
                data = await vnc_reader.read(1024)
                if not data:
                    break
                await websocket.send(data)
        except Exception as e:
            logger.error(f"Erreur VNC->WebSocket {connection_id}: {e}")
    
    async def _cleanup_connection(self, connection_id: str):
        """Nettoie une connexion."""
        if connection_id in self.active_connections:
            conn = self.active_connections[connection_id]
            
            # Fermer les connexions SSH/VNC
            if 'ssh_writer' in conn:
                conn['ssh_writer'].close()
                await conn['ssh_writer'].wait_closed()
            
            if 'vnc_writer' in conn:
                conn['vnc_writer'].close()
                await conn['vnc_writer'].wait_closed()
            
            # Supprimer de la liste des connexions actives
            del self.active_connections[connection_id]
    
    def get_active_connections_for_vm(self, vm_id: str) -> list:
        """Retourne les connexions actives pour une VM."""
        return [
            conn for conn in self.active_connections.values()
            if conn.get('vm_id') == vm_id
        ]
    
    async def close_all_connections_for_vm(self, vm_id: str):
        """Ferme toutes les connexions pour une VM."""
        connections_to_close = [
            conn_id for conn_id, conn in self.active_connections.items()
            if conn.get('vm_id') == vm_id
        ]
        
        for conn_id in connections_to_close:
            await self._cleanup_connection(conn_id)


# Instance globale du service
websocket_proxy_service = WebSocketProxyService()

