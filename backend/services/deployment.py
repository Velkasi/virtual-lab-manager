import asyncio
from sqlalchemy.orm import Session
from models import Lab, VM, DeploymentLog
from .terraform_service import TerraformService
from .ansible_service import AnsibleService
import uuid


async def deploy_lab(lab_id: uuid.UUID, db: Session):
    """
    Déploie un laboratoire virtuel en utilisant Terraform et Ansible.
    Cette fonction est exécutée en arrière-plan.
    """
    terraform_service = TerraformService()
    ansible_service = AnsibleService()
    
    try:
        # Récupérer le lab depuis la base de données
        lab = db.query(Lab).filter(Lab.id == lab_id).first()
        if not lab:
            return
        
        # Mettre à jour le statut
        lab.status = "deploying"
        db.commit()
        
        # Étape 1: Déployer avec Terraform
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="deployment",
            content="Début du déploiement avec Terraform..."
        )
        db.add(log_entry)
        db.commit()
        
        terraform_success = await terraform_service.deploy_lab(lab, db)
        
        if not terraform_success:
            lab.status = "error"
            db.commit()
            return
        
        # Étape 2: Configurer avec Ansible (si configuré)
        ansible_config_exists = any(vm.ansible_config_yaml for vm in lab.vms)
        
        if ansible_config_exists:
            log_entry = DeploymentLog(
                lab_id=lab_id,
                log_type="deployment",
                content="Configuration avec Ansible..."
            )
            db.add(log_entry)
            db.commit()
            
            ansible_success = await ansible_service.configure_lab(lab, db)
            
            if not ansible_success:
                lab.status = "error"
                db.commit()
                return
        
        # Mettre à jour le statut du lab
        lab.status = "deployed"
        db.commit()
        
        log_entry = DeploymentLog(
            lab_id=lab_id,
            log_type="deployment",
            content="Déploiement terminé avec succès!"
        )
        db.add(log_entry)
        db.commit()
        
    except Exception as e:
        # En cas d'erreur, mettre à jour le statut
        lab.status = "error"
        db.commit()
        
        # Logger l'erreur
        error_log = DeploymentLog(
            lab_id=lab_id,
            log_type="error",
            content=f"Erreur de déploiement: {str(e)}"
        )
        db.add(error_log)
        db.commit()


async def destroy_lab(lab_id: uuid.UUID, db: Session):
    """Détruit l'infrastructure d'un laboratoire."""
    terraform_service = TerraformService()
    
    try:
        lab = db.query(Lab).filter(Lab.id == lab_id).first()
        if not lab:
            return
        
        # Détruire l'infrastructure Terraform
        success = await terraform_service.destroy_lab(lab, db)
        
        if success:
            # Mettre à jour le statut des VMs
            for vm in lab.vms:
                vm.status = "deleted"
            
            lab.status = "deleted"
            db.commit()
        
        return success
        
    except Exception as e:
        error_log = DeploymentLog(
            lab_id=lab_id,
            log_type="error",
            content=f"Erreur lors de la destruction: {str(e)}"
        )
        db.add(error_log)
        db.commit()
        return False

