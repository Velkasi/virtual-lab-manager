import asyncio
import subprocess
import os
import tempfile
import json
from pathlib import Path
from sqlalchemy.orm import Session
from models import Lab, VM, DeploymentLog
import uuid


class TerraformService:
    def __init__(self):
        self.base_images_path = "/var/lib/libvirt/images"
        
    async def deploy_lab(self, lab: Lab, db: Session):
        """Déploie un laboratoire avec Terraform."""
        try:
            # Créer un répertoire de travail pour ce lab
            work_dir = f"/tmp/terraform_lab_{lab.id}"
            os.makedirs(work_dir, exist_ok=True)
            
            # Générer la configuration Terraform
            tf_config = self.generate_terraform_config(lab)
            tf_file_path = os.path.join(work_dir, "main.tf")
            
            with open(tf_file_path, 'w') as f:
                f.write(tf_config)
            
            # Initialiser Terraform
            await self._run_terraform_command(
                ["terraform", "init"], work_dir, lab.id, db
            )
            
            # Planifier le déploiement
            await self._run_terraform_command(
                ["terraform", "plan"], work_dir, lab.id, db
            )
            
            # Appliquer le déploiement
            await self._run_terraform_command(
                ["terraform", "apply", "-auto-approve"], work_dir, lab.id, db
            )
            
            # Récupérer les outputs
            output_result = await self._run_terraform_command(
                ["terraform", "output", "-json"], work_dir, lab.id, db
            )
            
            # Parser les outputs et mettre à jour les VMs
            await self._update_vms_from_outputs(lab, output_result, db)
            
            return True
            
        except Exception as e:
            await self._log_error(lab.id, f"Erreur Terraform: {str(e)}", db)
            return False
    
    def generate_terraform_config(self, lab: Lab) -> str:
        """Génère la configuration Terraform pour un lab."""
        
        config = '''terraform {
  required_providers {
    libvirt = {
      source = "dmacvicar/libvirt"
      version = "~> 0.7"
    }
  }
}

provider "libvirt" {
  uri = "qemu:///system"
}

# Pool de stockage par défaut
resource "libvirt_pool" "default" {
  name = "default"
  type = "dir"
  path = "/var/lib/libvirt/images"
}

# Réseau par défaut
resource "libvirt_network" "lab_network" {
  name      = "lab_''' + str(lab.id).replace('-', '_') + '''"
  mode      = "nat"
  domain    = "lab.local"
  addresses = ["192.168.100.0/24"]
  
  dhcp {
    enabled = true
  }
  
  dns {
    enabled = true
  }
}

'''
        
        # Générer les ressources pour chaque VM
        for i, vm in enumerate(lab.vms):
            vm_name = f"lab_{str(lab.id).replace('-', '_')}_{vm.name}".replace(" ", "_").replace("-", "_")
            
            # Image de base selon l'OS
            base_image_url = self._get_base_image_url(vm.os_image)
            
            config += f'''
# VM: {vm.name}
resource "libvirt_volume" "{vm_name}_base" {{
  name   = "{vm_name}_base.qcow2"
  pool   = libvirt_pool.default.name
  source = "{base_image_url}"
  format = "qcow2"
}}

resource "libvirt_volume" "{vm_name}_disk" {{
  name           = "{vm_name}_disk.qcow2"
  pool           = libvirt_pool.default.name
  base_volume_id = libvirt_volume.{vm_name}_base.id
  size           = {vm.disk_gb * 1024 * 1024 * 1024}
  format         = "qcow2"
}}

# Configuration cloud-init pour {vm.name}
data "template_file" "{vm_name}_user_data" {{
  template = file("${{path.module}}/cloud_init.yml")
  vars = {{
    hostname = "{vm.name}"
    ssh_port = {22000 + i}
  }}
}}

resource "libvirt_cloudinit_disk" "{vm_name}_cloudinit" {{
  name      = "{vm_name}_cloudinit.iso"
  pool      = libvirt_pool.default.name
  user_data = data.template_file.{vm_name}_user_data.rendered
}}

resource "libvirt_domain" "{vm_name}" {{
  name   = "{vm_name}"
  memory = "{vm.ram_mb}"
  vcpu   = {vm.vcpu}
  
  cloudinit = libvirt_cloudinit_disk.{vm_name}_cloudinit.id

  network_interface {{
    network_id     = libvirt_network.lab_network.id
    wait_for_lease = true
  }}

  disk {{
    volume_id = libvirt_volume.{vm_name}_disk.id
  }}

  console {{
    type        = "pty"
    target_port = "0"
    target_type = "serial"
  }}

  graphics {{
    type        = "vnc"
    listen_type = "address"
    address     = "0.0.0.0"
    autoport    = true
  }}
}}

output "{vm_name}_ip" {{
  value = libvirt_domain.{vm_name}.network_interface[0].addresses[0]
}}

output "{vm_name}_vnc_port" {{
  value = libvirt_domain.{vm_name}.graphics[0].port
}}

'''
        
        return config
    
    def _get_base_image_url(self, os_image: str) -> str:
        """Retourne l'URL de l'image de base selon l'OS."""
        images = {
            "ubuntu-22.04": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img",
            "ubuntu-20.04": "https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-amd64.img",
            "centos-stream-9": "https://cloud.centos.org/centos/9-stream/x86_64/images/CentOS-Stream-GenericCloud-9-latest.x86_64.qcow2",
            "debian-12": "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2",
            "fedora-39": "https://download.fedoraproject.org/pub/fedora/linux/releases/39/Cloud/x86_64/images/Fedora-Cloud-Base-39-1.5.x86_64.qcow2"
        }
        return images.get(os_image, images["ubuntu-22.04"])
    
    async def _run_terraform_command(self, command: list, working_dir: str, lab_id: uuid.UUID, db: Session) -> str:
        """Exécute une commande Terraform et log la sortie."""
        
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "TF_LOG": "INFO"}
        )
        
        output, _ = await process.communicate()
        output_str = output.decode('utf-8')
        
        # Logger la sortie
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="terraform",
            content=f"Command: {' '.join(command)}\n{output_str}"
        )
        db.add(log_entry)
        db.commit()
        
        if process.returncode != 0:
            raise Exception(f"Terraform command failed: {output_str}")
        
        return output_str
    
    async def _update_vms_from_outputs(self, lab: Lab, output_json: str, db: Session):
        """Met à jour les VMs avec les informations de Terraform."""
        try:
            outputs = json.loads(output_json)
            
            for vm in lab.vms:
                vm_name = f"lab_{str(lab.id).replace('-', '_')}_{vm.name}".replace(" ", "_").replace("-", "_")
                
                # Récupérer l'IP
                ip_key = f"{vm_name}_ip"
                if ip_key in outputs:
                    # Stocker l'IP dans un champ personnalisé ou utiliser un autre moyen
                    pass
                
                # Récupérer le port VNC
                vnc_port_key = f"{vm_name}_vnc_port"
                if vnc_port_key in outputs:
                    vm.vnc_port = outputs[vnc_port_key]["value"]
                
                # Assigner un port SSH unique
                vm.ssh_port = 22000 + lab.vms.index(vm)
                vm.status = "running"
            
            db.commit()
            
        except Exception as e:
            await self._log_error(lab.id, f"Erreur lors de la mise à jour des VMs: {str(e)}", db)
    
    async def _log_error(self, lab_id: uuid.UUID, error_message: str, db: Session):
        """Log une erreur."""
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="terraform",
            content=f"ERROR: {error_message}"
        )
        db.add(log_entry)
        db.commit()
    
    async def destroy_lab(self, lab: Lab, db: Session):
        """Détruit l'infrastructure d'un lab."""
        try:
            work_dir = f"/tmp/terraform_lab_{lab.id}"
            
            if os.path.exists(work_dir):
                await self._run_terraform_command(
                    ["terraform", "destroy", "-auto-approve"], work_dir, lab.id, db
                )
                
                # Nettoyer le répertoire de travail
                import shutil
                shutil.rmtree(work_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            await self._log_error(lab.id, f"Erreur lors de la destruction: {str(e)}", db)
            return False

