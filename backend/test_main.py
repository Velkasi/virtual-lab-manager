import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

from main import app
from database import get_db, Base
from models import Lab, VM

# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override de la dépendance de base de données
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Créer les tables de test
Base.metadata.create_all(bind=engine)

client = TestClient(app)


class TestAPI:
    """Tests pour l'API principale."""
    
    def test_root_endpoint(self):
        """Test de l'endpoint racine."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Virtual Lab Manager API"}
    
    def test_health_check(self):
        """Test du health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestLabsAPI:
    """Tests pour l'API des laboratoires."""
    
    def setup_method(self):
        """Nettoyer la base de données avant chaque test."""
        db = TestingSessionLocal()
        db.query(VM).delete()
        db.query(Lab).delete()
        db.commit()
        db.close()
    
    def test_create_lab(self):
        """Test de création d'un laboratoire."""
        lab_data = {
            "name": "Test Lab",
            "description": "Un laboratoire de test",
            "vms": [
                {
                    "name": "vm-test-1",
                    "vcpu": 2,
                    "ram_mb": 2048,
                    "disk_gb": 20,
                    "os_image": "ubuntu-22.04"
                }
            ]
        }
        
        response = client.post("/api/v1/labs/", json=lab_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == "Test Lab"
        assert data["description"] == "Un laboratoire de test"
        assert data["status"] == "pending"
        assert len(data["vms"]) == 1
        assert data["vms"][0]["name"] == "vm-test-1"
    
    def test_get_labs(self):
        """Test de récupération des laboratoires."""
        # Créer un lab d'abord
        lab_data = {
            "name": "Test Lab",
            "description": "Test",
            "vms": []
        }
        client.post("/api/v1/labs/", json=lab_data)
        
        # Récupérer les labs
        response = client.get("/api/v1/labs/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Lab"
    
    def test_get_lab_by_id(self):
        """Test de récupération d'un laboratoire par ID."""
        # Créer un lab
        lab_data = {
            "name": "Test Lab",
            "description": "Test",
            "vms": []
        }
        create_response = client.post("/api/v1/labs/", json=lab_data)
        lab_id = create_response.json()["id"]
        
        # Récupérer le lab par ID
        response = client.get(f"/api/v1/labs/{lab_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == lab_id
        assert data["name"] == "Test Lab"
    
    def test_get_nonexistent_lab(self):
        """Test de récupération d'un laboratoire inexistant."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/labs/{fake_id}")
        assert response.status_code == 404
    
    def test_delete_lab(self):
        """Test de suppression d'un laboratoire."""
        # Créer un lab
        lab_data = {
            "name": "Test Lab",
            "description": "Test",
            "vms": []
        }
        create_response = client.post("/api/v1/labs/", json=lab_data)
        lab_id = create_response.json()["id"]
        
        # Supprimer le lab
        response = client.delete(f"/api/v1/labs/{lab_id}")
        assert response.status_code == 200
        
        # Vérifier qu'il n'existe plus
        get_response = client.get(f"/api/v1/labs/{lab_id}")
        assert get_response.status_code == 404


class TestVMsAPI:
    """Tests pour l'API des machines virtuelles."""
    
    def setup_method(self):
        """Nettoyer la base de données avant chaque test."""
        db = TestingSessionLocal()
        db.query(VM).delete()
        db.query(Lab).delete()
        db.commit()
        db.close()
    
    def test_get_vms_by_lab(self):
        """Test de récupération des VMs d'un laboratoire."""
        # Créer un lab avec des VMs
        lab_data = {
            "name": "Test Lab",
            "description": "Test",
            "vms": [
                {
                    "name": "vm-1",
                    "vcpu": 2,
                    "ram_mb": 2048,
                    "disk_gb": 20,
                    "os_image": "ubuntu-22.04"
                },
                {
                    "name": "vm-2",
                    "vcpu": 4,
                    "ram_mb": 4096,
                    "disk_gb": 50,
                    "os_image": "centos-stream-9"
                }
            ]
        }
        create_response = client.post("/api/v1/labs/", json=lab_data)
        lab_id = create_response.json()["id"]
        
        # Récupérer les VMs
        response = client.get(f"/api/v1/vms/lab/{lab_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "vm-1"
        assert data[1]["name"] == "vm-2"
    
    def test_vm_actions_without_deployment(self):
        """Test des actions sur une VM non déployée."""
        # Créer un lab avec une VM
        lab_data = {
            "name": "Test Lab",
            "description": "Test",
            "vms": [
                {
                    "name": "vm-test",
                    "vcpu": 2,
                    "ram_mb": 2048,
                    "disk_gb": 20,
                    "os_image": "ubuntu-22.04"
                }
            ]
        }
        create_response = client.post("/api/v1/labs/", json=lab_data)
        vm_id = create_response.json()["vms"][0]["id"]
        
        # Tenter de démarrer une VM non déployée
        response = client.post(f"/api/v1/vms/{vm_id}/start")
        assert response.status_code == 400  # Erreur attendue


class TestValidation:
    """Tests de validation des données."""
    
    def test_create_lab_invalid_data(self):
        """Test de création d'un lab avec des données invalides."""
        # Nom manquant
        lab_data = {
            "description": "Test sans nom",
            "vms": []
        }
        response = client.post("/api/v1/labs/", json=lab_data)
        assert response.status_code == 422
        
        # VM avec spécifications invalides
        lab_data = {
            "name": "Test Lab",
            "vms": [
                {
                    "name": "vm-invalid",
                    "vcpu": 0,  # Invalide
                    "ram_mb": -1,  # Invalide
                    "disk_gb": 0,  # Invalide
                    "os_image": "unknown-os"
                }
            ]
        }
        response = client.post("/api/v1/labs/", json=lab_data)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])

