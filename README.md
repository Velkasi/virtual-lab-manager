# Virtual Lab Manager

Une application web complète pour la gestion et le déploiement de laboratoires virtuels avec interface React, backend Python, intégration Terraform/Ansible, et accès SSH/VNC intégré.

## Fonctionnalités

### Interface Web Intuitive
- Création et configuration de laboratoires virtuels personnalisés
- Gestion des machines virtuelles avec spécifications hardware définies
- Interface responsive compatible desktop et mobile
- Visualisation en temps réel du déploiement (logs Terraform et Ansible)

### Gestion des VMs
- Support de multiples VMs par laboratoire
- Configuration hardware personnalisable (CPU, RAM, disque)
- Choix d'images OS (Ubuntu, CentOS, Debian, Fedora)
- Gestion d'état des VMs (start/stop/restart)
- Persistance des données (pas de perte lors des redémarrages)

### Accès Intégré
- **SSH dans le navigateur** : Terminal interactif avec xterm.js
- **VNC dans le navigateur** : Accès graphique via WebSocket
- Connexions sécurisées et persistantes
- Support de connexions multiples simultanées

### Automatisation
- **Terraform** : Création automatique de l'infrastructure VM
- **Ansible** : Configuration logicielle via playbooks YAML
- Logs de déploiement en temps réel
- Templates de laboratoires prédéfinis

### Technologies
- **Backend** : Python FastAPI, PostgreSQL, WebSockets
- **Frontend** : React, Tailwind CSS, shadcn/ui
- **Infrastructure** : QEMU/KVM, libvirt
- **Automatisation** : Terraform, Ansible
- **Proxy** : Nginx avec support WebSocket

## Installation

### Prérequis
- Serveur Debian 11/12 ou Ubuntu 20.04/22.04
- 32 Go RAM minimum (recommandé)
- 200 Go SSD minimum
- Processeur avec support de virtualisation (Intel VT-x ou AMD-V)
- Accès root (sudo)

### Installation Automatique

```bash
# Cloner le projet
git clone <repository-url>
cd virtual-lab-manager

# Lancer l'installation (en tant que root)
sudo ./install.sh
```

Le script d'installation configure automatiquement :
- Tous les composants système nécessaires
- Base de données PostgreSQL
- Services systemd
- Configuration Nginx
- Firewall UFW
- Utilisateur système dédié

### Installation Manuelle

Si vous préférez une installation manuelle, consultez le fichier `install.sh` pour les étapes détaillées.

## Configuration

### Variables d'Environnement

Le fichier `.env` est créé automatiquement lors de l'installation :

```bash
# Configuration de la base de données
DATABASE_URL=postgresql://vlm_user:password@localhost/virtual_lab_manager

# Configuration de l'application
SECRET_KEY=<generated>
DEBUG=false
ALLOWED_HOSTS=localhost,127.0.0.1

# Configuration des chemins
TERRAFORM_PATH=/usr/bin/terraform
ANSIBLE_PATH=/usr/bin/ansible-playbook
LIBVIRT_URI=qemu:///system

# Configuration réseau
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Ports Réseau

- **80** : Interface web (Nginx)
- **8000** : API Backend (interne)
- **5432** : PostgreSQL (interne)
- **5900-5999** : Ports VNC des VMs
- **22000-22999** : Ports SSH des VMs

## Utilisation

### Accès à l'Application

Après installation, accédez à l'application via :
```
http://<ip-du-serveur>
```

### Création d'un Laboratoire

1. **Cliquer sur "Créer un Lab"**
2. **Remplir les informations générales** :
   - Nom du laboratoire
   - Description (optionnelle)

3. **Configurer les VMs** :
   - Nom de chaque VM
   - Spécifications hardware (vCPU, RAM, disque)
   - Image OS

4. **Configuration Ansible (optionnelle)** :
   - Coller un playbook YAML pour la configuration automatique

5. **Déployer** : Le système utilise Terraform pour créer les VMs et Ansible pour les configurer

### Gestion des VMs

- **Démarrer/Arrêter** : Contrôle de l'état des VMs
- **Accès SSH** : Terminal dans le navigateur
- **Accès VNC** : Bureau graphique dans le navigateur
- **Logs** : Visualisation des logs de déploiement

### Exemple de Playbook Ansible

```yaml
---
- hosts: all
  become: yes
  tasks:
    - name: Mettre à jour le système
      apt:
        update_cache: yes
        upgrade: dist

    - name: Installer Docker
      apt:
        name: docker.io
        state: present

    - name: Démarrer Docker
      systemd:
        name: docker
        state: started
        enabled: yes

    - name: Ajouter l'utilisateur au groupe docker
      user:
        name: ubuntu
        groups: docker
        append: yes
```

## Administration

### Commandes Utiles

```bash
# Statut des services
sudo systemctl status vlm-backend vlm-frontend

# Logs en temps réel
sudo journalctl -u vlm-backend -f
sudo journalctl -u vlm-frontend -f

# Redémarrer les services
sudo systemctl restart vlm-backend vlm-frontend nginx

# Vérifier les VMs libvirt
sudo virsh list --all
```

### Sauvegarde

```bash
# Sauvegarde automatique
sudo /opt/virtual-lab-manager/scripts/backup.sh

# Les sauvegardes sont stockées dans /opt/backups/virtual-lab-manager/
```

### Restauration

```bash
# Lister les sauvegardes disponibles
sudo /opt/virtual-lab-manager/scripts/restore.sh

# Restaurer une sauvegarde spécifique
sudo /opt/virtual-lab-manager/scripts/restore.sh 20241219_143000
```

### Mise à Jour

```bash
# Mise à jour automatique (avec sauvegarde)
sudo /opt/virtual-lab-manager/scripts/update.sh
```

## Dépannage

### Problèmes Courants

**Les VMs ne démarrent pas :**
- Vérifier que la virtualisation est activée dans le BIOS
- Contrôler les ressources disponibles (RAM, CPU)
- Vérifier les logs : `sudo journalctl -u libvirtd`

**Erreurs de connexion SSH/VNC :**
- Vérifier que les ports sont ouverts dans le firewall
- Contrôler le statut des VMs : `sudo virsh list`
- Vérifier les logs WebSocket dans le navigateur

**Erreurs de déploiement Terraform :**
- Vérifier les permissions libvirt : `sudo usermod -aG libvirt vlm`
- Contrôler l'espace disque disponible
- Vérifier les logs dans l'interface web

### Logs

```bash
# Logs de l'application
sudo journalctl -u vlm-backend -n 100
sudo journalctl -u vlm-frontend -n 100

# Logs système
sudo journalctl -u libvirtd -n 50
sudo journalctl -u nginx -n 50

# Logs des VMs
sudo virsh console <vm-name>
```

## Sécurité

### Recommandations

1. **Firewall** : Configuré automatiquement avec UFW
2. **Utilisateur dédié** : L'application s'exécute sous l'utilisateur `vlm`
3. **Base de données** : Accès local uniquement avec mot de passe fort
4. **SSL/TLS** : Configurer un certificat SSL pour la production
5. **Sauvegardes** : Programmer des sauvegardes régulières

### Configuration SSL (Production)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com

# Le certificat sera automatiquement renouvelé
```

## Support et Contribution

### Structure du Projet

```
virtual-lab-manager/
├── backend/                 # API FastAPI
│   ├── main.py             # Point d'entrée
│   ├── models.py           # Modèles SQLAlchemy
│   ├── routers/            # Endpoints API
│   └── services/           # Logique métier
├── frontend/               # Interface React
│   └── virtual-lab-frontend/
├── scripts/                # Scripts d'administration
├── docs/                   # Documentation technique
└── install.sh             # Script d'installation
```

### Développement

```bash
# Backend (développement)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend (développement)
cd frontend/virtual-lab-frontend
pnpm install
pnpm run dev
```

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Changelog

### Version 1.0.0
- Interface web complète pour la gestion des labs
- Intégration Terraform/Ansible
- Accès SSH/VNC dans le navigateur
- Scripts d'installation et d'administration
- Documentation complète

