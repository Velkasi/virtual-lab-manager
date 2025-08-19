import asyncio
import subprocess
from models import VM


async def start_vm(vm: VM) -> bool:
    """Démarre une machine virtuelle en utilisant virsh."""
    try:
        vm_name = f"{vm.lab.name}_{vm.name}".replace(" ", "_").replace("-", "_")
        
        process = await asyncio.create_subprocess_exec(
            "virsh", "start", vm_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            print(f"Erreur lors du démarrage de la VM {vm_name}: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Exception lors du démarrage de la VM: {str(e)}")
        return False


async def stop_vm(vm: VM) -> bool:
    """Arrête une machine virtuelle en utilisant virsh."""
    try:
        vm_name = f"{vm.lab.name}_{vm.name}".replace(" ", "_").replace("-", "_")
        
        process = await asyncio.create_subprocess_exec(
            "virsh", "shutdown", vm_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            print(f"Erreur lors de l'arrêt de la VM {vm_name}: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Exception lors de l'arrêt de la VM: {str(e)}")
        return False


async def restart_vm(vm: VM) -> bool:
    """Redémarre une machine virtuelle en utilisant virsh."""
    try:
        vm_name = f"{vm.lab.name}_{vm.name}".replace(" ", "_").replace("-", "_")
        
        process = await asyncio.create_subprocess_exec(
            "virsh", "reboot", vm_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True
        else:
            print(f"Erreur lors du redémarrage de la VM {vm_name}: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"Exception lors du redémarrage de la VM: {str(e)}")
        return False


async def get_vm_status(vm: VM) -> str:
    """Récupère le statut d'une machine virtuelle."""
    try:
        vm_name = f"{vm.lab.name}_{vm.name}".replace(" ", "_").replace("-", "_")
        
        process = await asyncio.create_subprocess_exec(
            "virsh", "domstate", vm_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            status = stdout.decode().strip()
            # Mapper les statuts virsh aux statuts de l'application
            if status == "running":
                return "running"
            elif status in ["shut off", "shutoff"]:
                return "stopped"
            else:
                return "unknown"
        else:
            return "error"
            
    except Exception as e:
        print(f"Exception lors de la récupération du statut de la VM: {str(e)}")
        return "error"


async def get_vm_info(vm: VM) -> dict:
    """Récupère les informations détaillées d'une machine virtuelle."""
    try:
        vm_name = f"{vm.lab.name}_{vm.name}".replace(" ", "_").replace("-", "_")
        
        process = await asyncio.create_subprocess_exec(
            "virsh", "dominfo", vm_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            info = {}
            for line in stdout.decode().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
        else:
            return {}
            
    except Exception as e:
        print(f"Exception lors de la récupération des infos de la VM: {str(e)}")
        return {}

