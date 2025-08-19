import asyncio
import subprocess
import os
import tempfile
import yaml
from pathlib import Path
from sqlalchemy.orm import Session
from models import Lab, VM, DeploymentLog
import uuid


class AnsibleService:
    def __init__(self):
        self.ansible_user = "ubuntu"
        self.ssh_key_path = "/home/ubuntu/.ssh/id_rsa"
    
    async def configure_lab(self, lab: Lab, db: Session):
        """Configure les VMs d'un lab avec Ansible."""
        try:
            # Vérifier s'il y a une configuration Ansible
            ansible_config = None
            for vm in lab.vms:
                if vm.ansible_config_yaml:
                    ansible_config = vm.ansible_config_yaml
                    break
            
            if not ansible_config:
                await self._log_info(lab.id, "Aucune configuration Ansible fournie, configuration ignorée", db)
                return True
            
            # Créer un répertoire de travail pour Ansible
            work_dir = f"/tmp/ansible_lab_{lab.id}"
            os.makedirs(work_dir, exist_ok=True)
            
            # Générer l'inventaire
            inventory_path = os.path.join(work_dir, "inventory.ini")
            self._generate_inventory(lab, inventory_path)
            
            # Créer le playbook
            playbook_path = os.path.join(work_dir, "playbook.yml")
            with open(playbook_path, 'w') as f:
                f.write(ansible_config)
            
            # Créer le fichier de configuration Ansible
            ansible_cfg_path = os.path.join(work_dir, "ansible.cfg")
            self._generate_ansible_config(ansible_cfg_path)
            
            # Attendre que les VMs soient accessibles
            await self._wait_for_vms_ready(lab, db)
            
            # Exécuter Ansible
            await self._run_ansible_command(
                ["ansible-playbook", "-i", inventory_path, playbook_path, "-v"],
                work_dir, lab.id, db
            )
            
            return True
            
        except Exception as e:
            await self._log_error(lab.id, f"Erreur Ansible: {str(e)}", db)
            return False
    
    def _generate_inventory(self, lab: Lab, inventory_path: str):
        """Génère l'inventaire Ansible pour un lab."""
        
        inventory_content = "[lab_vms]\n"
        
        for vm in lab.vms:
            # Utiliser l'IP locale pour SSH via port forwarding
            inventory_content += f"{vm.name} ansible_host=localhost ansible_port={vm.ssh_port} ansible_user={self.ansible_user}\n"
        
        inventory_content += "\n[lab_vms:vars]\n"
        inventory_content += "ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'\n"
        
        with open(inventory_path, 'w') as f:
            f.write(inventory_content)
    
    def _generate_ansible_config(self, config_path: str):
        """Génère le fichier de configuration Ansible."""
        
        config_content = """[defaults]
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = memory
stdout_callback = yaml
callback_whitelist = timer, profile_tasks

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
pipelining = True
"""
        
        with open(config_path, 'w') as f:
            f.write(config_content)
    
    async def _wait_for_vms_ready(self, lab: Lab, db: Session, timeout: int = 300):
        """Attend que les VMs soient prêtes pour SSH."""
        
        await self._log_info(lab.id, "Attente que les VMs soient prêtes pour SSH...", db)
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            all_ready = True
            
            for vm in lab.vms:
                if not vm.ssh_port:
                    all_ready = False
                    continue
                
                # Tester la connexion SSH
                try:
                    process = await asyncio.create_subprocess_exec(
                        "nc", "-z", "localhost", str(vm.ssh_port),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    await asyncio.wait_for(process.communicate(), timeout=5)
                    
                    if process.returncode != 0:
                        all_ready = False
                
                except (asyncio.TimeoutError, Exception):
                    all_ready = False
            
            if all_ready:
                await self._log_info(lab.id, "Toutes les VMs sont prêtes pour SSH", db)
                break
            
            # Vérifier le timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise Exception(f"Timeout: Les VMs ne sont pas prêtes après {timeout} secondes")
            
            await asyncio.sleep(10)
    
    async def _run_ansible_command(self, command: list, working_dir: str, lab_id: uuid.UUID, db: Session):
        """Exécute une commande Ansible et log la sortie."""
        
        env = {
            **os.environ,
            "ANSIBLE_CONFIG": os.path.join(working_dir, "ansible.cfg"),
            "ANSIBLE_HOST_KEY_CHECKING": "False"
        }
        
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=env
        )
        
        output, _ = await process.communicate()
        output_str = output.decode('utf-8')
        
        # Logger la sortie
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="ansible",
            content=f"Command: {' '.join(command)}\n{output_str}"
        )
        db.add(log_entry)
        db.commit()
        
        if process.returncode != 0:
            raise Exception(f"Ansible command failed: {output_str}")
        
        return output_str
    
    async def _log_info(self, lab_id: uuid.UUID, message: str, db: Session):
        """Log une information."""
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="ansible",
            content=f"INFO: {message}"
        )
        db.add(log_entry)
        db.commit()
    
    async def _log_error(self, lab_id: uuid.UUID, error_message: str, db: Session):
        """Log une erreur."""
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="ansible",
            content=f"ERROR: {error_message}"
        )
        db.add(log_entry)
        db.commit()
    
    def validate_playbook(self, playbook_yaml: str) -> tuple[bool, str]:
        """Valide un playbook Ansible."""
        try:
            # Parser le YAML
            playbook = yaml.safe_load(playbook_yaml)
            
            # Vérifications de base
            if not isinstance(playbook, list):
                return False, "Le playbook doit être une liste de plays"
            
            for play in playbook:
                if not isinstance(play, dict):
                    return False, "Chaque play doit être un dictionnaire"
                
                if 'hosts' not in play:
                    return False, "Chaque play doit avoir un champ 'hosts'"
                
                if 'tasks' not in play and 'roles' not in play:
                    return False, "Chaque play doit avoir des 'tasks' ou des 'roles'"
            
            return True, "Playbook valide"
            
        except yaml.YAMLError as e:
            return False, f"Erreur YAML: {str(e)}"
        except Exception as e:
            return False, f"Erreur de validation: {str(e)}"

