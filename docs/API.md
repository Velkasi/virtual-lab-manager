# Documentation API - Virtual Lab Manager

## Vue d'ensemble

L'API Virtual Lab Manager est une API REST construite avec FastAPI qui permet la gestion complète des laboratoires virtuels et de leurs machines virtuelles.

**Base URL :** `http://localhost:8000/api/v1`

## Authentification

*Note : L'authentification n'est pas encore implémentée dans cette version.*

## Endpoints

### Laboratoires

#### GET /labs
Récupère la liste de tous les laboratoires.

**Réponse :**
```json
[
  {
    "id": "uuid",
    "name": "Mon Lab",
    "description": "Description du laboratoire",
    "status": "deployed",
    "created_at": "2024-12-19T10:30:00Z",
    "updated_at": "2024-12-19T11:00:00Z",
    "vms": [...]
  }
]
```

**Statuts possibles :**
- `pending` : En attente de déploiement
- `deploying` : Déploiement en cours
- `deployed` : Déployé avec succès
- `error` : Erreur de déploiement
- `deleted` : Supprimé

#### POST /labs
Crée un nouveau laboratoire.

**Corps de la requête :**
```json
{
  "name": "Mon Nouveau Lab",
  "description": "Description optionnelle",
  "vms": [
    {
      "name": "vm-web",
      "vcpu": 2,
      "ram_mb": 2048,
      "disk_gb": 20,
      "os_image": "ubuntu-22.04",
      "ansible_config_yaml": "---\n- hosts: all\n  tasks:\n    - name: Install nginx\n      apt: name=nginx state=present"
    }
  ]
}
```

**Réponse :** `201 Created`
```json
{
  "id": "uuid",
  "name": "Mon Nouveau Lab",
  "description": "Description optionnelle",
  "status": "pending",
  "created_at": "2024-12-19T10:30:00Z",
  "updated_at": "2024-12-19T10:30:00Z",
  "vms": [...]
}
```

#### GET /labs/{lab_id}
Récupère les détails d'un laboratoire spécifique.

**Paramètres :**
- `lab_id` (UUID) : Identifiant du laboratoire

**Réponse :** `200 OK`
```json
{
  "id": "uuid",
  "name": "Mon Lab",
  "description": "Description",
  "status": "deployed",
  "created_at": "2024-12-19T10:30:00Z",
  "updated_at": "2024-12-19T11:00:00Z",
  "vms": [...]
}
```

#### POST /labs/{lab_id}/deploy
Déclenche le déploiement d'un laboratoire.

**Paramètres :**
- `lab_id` (UUID) : Identifiant du laboratoire

**Réponse :** `200 OK`
```json
{
  "message": "Déploiement démarré",
  "lab_id": "uuid"
}
```

#### DELETE /labs/{lab_id}
Supprime un laboratoire et toutes ses VMs.

**Paramètres :**
- `lab_id` (UUID) : Identifiant du laboratoire

**Réponse :** `200 OK`
```json
{
  "message": "Laboratoire supprimé avec succès"
}
```

#### GET /labs/{lab_id}/logs
Récupère les logs de déploiement d'un laboratoire.

**Paramètres :**
- `lab_id` (UUID) : Identifiant du laboratoire
- `log_type` (query, optionnel) : Type de log (`terraform`, `ansible`, `deployment`, `error`)

**Réponse :** `200 OK`
```json
[
  {
    "id": 1,
    "lab_id": "uuid",
    "log_type": "terraform",
    "content": "Terraform output...",
    "created_at": "2024-12-19T10:35:00Z"
  }
]
```

### Machines Virtuelles

#### GET /vms/lab/{lab_id}
Récupère toutes les VMs d'un laboratoire.

**Paramètres :**
- `lab_id` (UUID) : Identifiant du laboratoire

**Réponse :** `200 OK`
```json
[
  {
    "id": "uuid",
    "lab_id": "uuid",
    "name": "vm-web",
    "vcpu": 2,
    "ram_mb": 2048,
    "disk_gb": 20,
    "os_image": "ubuntu-22.04",
    "status": "running",
    "ssh_port": 22001,
    "vnc_port": 5901,
    "created_at": "2024-12-19T10:30:00Z",
    "updated_at": "2024-12-19T11:00:00Z"
  }
]
```

**Statuts des VMs :**
- `pending` : En attente de création
- `creating` : Création en cours
- `stopped` : Arrêtée
- `running` : En cours d'exécution
- `error` : Erreur
- `deleted` : Supprimée

#### GET /vms/{vm_id}
Récupère les détails d'une VM spécifique.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "id": "uuid",
  "lab_id": "uuid",
  "name": "vm-web",
  "vcpu": 2,
  "ram_mb": 2048,
  "disk_gb": 20,
  "os_image": "ubuntu-22.04",
  "status": "running",
  "ssh_port": 22001,
  "vnc_port": 5901,
  "ansible_config_yaml": "...",
  "created_at": "2024-12-19T10:30:00Z",
  "updated_at": "2024-12-19T11:00:00Z"
}
```

#### POST /vms/{vm_id}/start
Démarre une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "message": "VM démarrée avec succès",
  "vm_id": "uuid",
  "status": "running"
}
```

#### POST /vms/{vm_id}/stop
Arrête une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "message": "VM arrêtée avec succès",
  "vm_id": "uuid",
  "status": "stopped"
}
```

#### POST /vms/{vm_id}/restart
Redémarre une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "message": "VM redémarrée avec succès",
  "vm_id": "uuid",
  "status": "running"
}
```

#### GET /vms/{vm_id}/ssh-access
Récupère les informations de connexion SSH.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "host": "localhost",
  "port": 22001,
  "username": "ubuntu",
  "status": "available"
}
```

#### GET /vms/{vm_id}/vnc-access
Récupère les informations de connexion VNC.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "host": "localhost",
  "port": 5901,
  "status": "available"
}
```

### WebSockets

#### WS /ws/ssh/{vm_id}
Établit une connexion SSH WebSocket vers une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Protocole :**
- Messages entrants : Commandes SSH (texte)
- Messages sortants : Sortie SSH (texte)

**Exemple d'utilisation JavaScript :**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/ssh/vm-uuid');

ws.onopen = () => {
  console.log('Connexion SSH établie');
};

ws.onmessage = (event) => {
  console.log('Sortie SSH:', event.data);
};

ws.send('ls -la\n');
```

#### WS /ws/vnc/{vm_id}
Établit une connexion VNC WebSocket vers une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Protocole :**
- Messages entrants : Données VNC (binaire)
- Messages sortants : Données VNC (binaire)

### Utilitaires

#### GET /
Point d'entrée de l'API.

**Réponse :** `200 OK`
```json
{
  "message": "Virtual Lab Manager API"
}
```

#### GET /health
Vérification de santé de l'API.

**Réponse :** `200 OK`
```json
{
  "status": "healthy"
}
```

#### GET /connections/{vm_id}
Récupère les connexions actives pour une VM.

**Paramètres :**
- `vm_id` (UUID) : Identifiant de la VM

**Réponse :** `200 OK`
```json
{
  "vm_id": "uuid",
  "active_connections": 2,
  "connections": [
    {
      "type": "ssh",
      "connection_time": "N/A"
    },
    {
      "type": "vnc",
      "connection_time": "N/A"
    }
  ]
}
```

## Codes d'Erreur

### Codes HTTP Standard

- `200 OK` : Succès
- `201 Created` : Ressource créée
- `400 Bad Request` : Requête invalide
- `404 Not Found` : Ressource non trouvée
- `422 Unprocessable Entity` : Erreur de validation
- `500 Internal Server Error` : Erreur serveur

### Format des Erreurs

```json
{
  "detail": "Description de l'erreur"
}
```

### Erreurs de Validation (422)

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Images OS Supportées

- `ubuntu-22.04` : Ubuntu 22.04 LTS
- `ubuntu-20.04` : Ubuntu 20.04 LTS
- `centos-stream-9` : CentOS Stream 9
- `debian-12` : Debian 12
- `fedora-39` : Fedora 39

## Limites

- **VMs par laboratoire :** Pas de limite technique, mais limitée par les ressources système
- **Taille des playbooks Ansible :** 1 MB maximum
- **Connexions WebSocket simultanées :** Limitée par les ressources système
- **Ports SSH :** 22000-22999 (1000 VMs maximum)
- **Ports VNC :** 5900-5999 (100 VMs maximum)

## Exemples d'Utilisation

### Créer un laboratoire simple

```bash
curl -X POST "http://localhost:8000/api/v1/labs/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lab de Test",
    "description": "Un laboratoire simple pour les tests",
    "vms": [
      {
        "name": "vm-test",
        "vcpu": 2,
        "ram_mb": 2048,
        "disk_gb": 20,
        "os_image": "ubuntu-22.04"
      }
    ]
  }'
```

### Déployer un laboratoire

```bash
curl -X POST "http://localhost:8000/api/v1/labs/{lab_id}/deploy"
```

### Récupérer les logs de déploiement

```bash
curl "http://localhost:8000/api/v1/labs/{lab_id}/logs?log_type=terraform"
```

### Démarrer une VM

```bash
curl -X POST "http://localhost:8000/api/v1/vms/{vm_id}/start"
```

