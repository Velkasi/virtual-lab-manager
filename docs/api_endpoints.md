# API RESTful Endpoints

## Labs

### `POST /api/v1/labs`
- **Description**: Crée un nouveau laboratoire virtuel.
- **Request Body**: 
  ```json
  {
    "name": "string",
    "description": "string",
    "vms": [
      {
        "name": "string",
        "vcpu": "integer",
        "ram_mb": "integer",
        "disk_gb": "integer",
        "os_image": "string"
      }
    ],
    "ansible_config_yaml": "string" (optional)
  }
  ```
- **Response**: `Lab` object

### `GET /api/v1/labs`
- **Description**: Liste tous les laboratoires virtuels.
- **Response**: Array of `Lab` objects

### `GET /api/v1/labs/{lab_id}`
- **Description**: Récupère les détails d'un laboratoire spécifique.
- **Response**: `Lab` object

### `DELETE /api/v1/labs/{lab_id}`
- **Description**: Supprime un laboratoire virtuel.
- **Response**: Success message

### `POST /api/v1/labs/{lab_id}/deploy`
- **Description**: Déclenche le déploiement d'un laboratoire virtuel.
- **Response**: Success message

### `GET /api/v1/labs/{lab_id}/logs`
- **Description**: Récupère les logs de déploiement (Terraform/Ansible) pour un laboratoire.
- **Response**: `Log` object

## VMs

### `GET /api/v1/vms`
- **Description**: Liste toutes les machines virtuelles (peut être filtré par `lab_id`).
- **Response**: Array of `VM` objects

### `GET /api/v1/vms/{vm_id}`
- **Description**: Récupère les détails d'une machine virtuelle spécifique.
- **Response**: `VM` object

### `POST /api/v1/vms/{vm_id}/start`
- **Description**: Démarre une machine virtuelle.
- **Response**: Success message

### `POST /api/v1/vms/{vm_id}/stop`
- **Description**: Arrête une machine virtuelle.
- **Response**: Success message

### `POST /api/v1/vms/{vm_id}/restart`
- **Description**: Redémarre une machine virtuelle.
- **Response**: Success message

### `GET /api/v1/vms/{vm_id}/ssh_access`
- **Description**: Récupère les informations de connexion SSH pour une VM.
- **Response**: `SSHConnectionInfo` object

### `GET /api/v1/vms/{vm_id}/vnc_access`
- **Description**: Récupère les informations de connexion VNC pour une VM.
- **Response**: `VNCConnectionInfo` object


