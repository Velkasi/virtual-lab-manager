#!/bin/bash

# Virtual Lab Manager - Script d'installation pour Debian
# Ce script installe et configure tous les composants nécessaires

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
INSTALL_DIR="/opt/virtual-lab-manager"
SERVICE_USER="vlm"
DB_NAME="virtual_lab_manager"
DB_USER="vlm_user"
DB_PASSWORD=$(openssl rand -base64 32)

# Fonction d'affichage
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Vérification des privilèges root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
}

# Vérification de la distribution
check_debian() {
    if ! grep -q "Debian\|Ubuntu" /etc/os-release; then
        error "Ce script est conçu pour Debian/Ubuntu uniquement"
    fi
    log "Distribution compatible détectée"
}

# Mise à jour du système
update_system() {
    log "Mise à jour du système..."
    apt update && apt upgrade -y
    apt install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates passwd
}

# Installation de Python et pip
install_python() {
    log "Installation de Python 3.11 et pip..."
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    
    # Créer un lien symbolique pour python3
    if ! command -v python3 &> /dev/null; then
        ln -sf /usr/bin/python3.11 /usr/bin/python3
    fi
}

# Installation de Node.js
install_nodejs() {
    log "Installation de Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
    
    # Installation de pnpm
    npm install -g pnpm
    
    log "Node.js $(node --version) et pnpm installés"
}

# Installation de PostgreSQL
install_postgresql() {
    log "Installation de PostgreSQL..."
    apt install -y postgresql postgresql-contrib
    
    # Démarrer et activer PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Créer la base de données et l'utilisateur
    log "Configuration de la base de données..."
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    
    log "Base de données PostgreSQL configurée"
}

# Installation de Terraform
install_terraform() {
    log "Installation de Terraform..."
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
    apt update
    apt install -y terraform
    
    log "Terraform $(terraform --version | head -n1) installé"
}

# Installation d'Ansible
install_ansible() {
    log "Installation d'Ansible..."
    apt install -y ansible
    
    log "Ansible $(ansible --version | head -n1) installé"
}

# Installation de QEMU/KVM et libvirt
install_virtualization() {
    log "Installation de QEMU/KVM et libvirt..."
    apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
    
    # Ajouter l'utilisateur au groupe libvirt
    usermod -aG libvirt $SERVICE_USER 2>/dev/null || true
    
    # Démarrer et activer libvirt
    systemctl start libvirtd
    systemctl enable libvirtd
    
    # Vérifier que la virtualisation fonctionne
    if ! virt-host-validate qemu >/dev/null 2>&1; then
        warn "La virtualisation matérielle pourrait ne pas être disponible"
    fi
    
    log "Virtualisation QEMU/KVM configurée"
}

# Installation de noVNC
install_novnc() {
    log "Installation de noVNC..."
    apt install -y novnc websockify
    
    # Créer le répertoire pour noVNC
    mkdir -p /opt/novnc
    
    # Cloner noVNC si pas déjà présent
    if [ ! -d "/opt/novnc/noVNC" ]; then
        git clone https://github.com/novnc/noVNC.git /opt/novnc/noVNC
        git clone https://github.com/novnc/websockify.git /opt/novnc/websockify
    fi
    
    log "noVNC installé"
}

# Création de l'utilisateur système
create_user() {
    log "Création de l'utilisateur système $SERVICE_USER..."

    # Créer les groupes si nécessaire
    for grp in libvirt kvm; do
        if ! getent group $grp >/dev/null; then
            groupadd $grp
        fi
    done

    # Créer l'utilisateur si il n'existe pas
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d /home/$SERVICE_USER -m $SERVICE_USER
        usermod -aG libvirt,kvm $SERVICE_USER
    fi

    # Créer les répertoires nécessaires
    mkdir -p /home/$SERVICE_USER/.ssh
    chown -R $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER

    log "Utilisateur $SERVICE_USER créé"
}

# Installation de l'application
install_application() {
    log "Installation de l'application Virtual Lab Manager..."
    
    # Créer le répertoire d'installation
    mkdir -p $INSTALL_DIR
    
    # Copier les fichiers de l'application
    cp -r . $INSTALL_DIR/
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
    
    # Installation des dépendances Python
    log "Installation des dépendances Python..."
    cd $INSTALL_DIR/backend
    sudo -u $SERVICE_USER python3 -m venv venv
    sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt
    
    # Installation des dépendances Node.js
    log "Installation des dépendances Node.js..."
    cd $INSTALL_DIR/frontend/virtual-lab-frontend
    sudo -u $SERVICE_USER pnpm install
    
    # Build du frontend
    log "Build du frontend..."
    sudo -u $SERVICE_USER pnpm run build
    
    log "Application installée dans $INSTALL_DIR"
}

# Configuration des variables d'environnement
configure_environment() {
    log "Configuration des variables d'environnement..."
    
    cat > $INSTALL_DIR/.env << EOF
# Configuration de la base de données
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME

# Configuration de l'application
SECRET_KEY=$(openssl rand -base64 32)
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
EOF
    
    chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/.env
    chmod 600 $INSTALL_DIR/.env
    
    log "Variables d'environnement configurées"
}

# Création des services systemd
create_services() {
    log "Création des services systemd..."
    
    # Service backend
    cat > /etc/systemd/system/vlm-backend.service << EOF
[Unit]
Description=Virtual Lab Manager Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/backend/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Service frontend (nginx sera utilisé en production)
    cat > /etc/systemd/system/vlm-frontend.service << EOF
[Unit]
Description=Virtual Lab Manager Frontend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/frontend/virtual-lab-frontend
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/pnpm run preview --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Recharger systemd
    systemctl daemon-reload
    
    log "Services systemd créés"
}

# Installation et configuration de Nginx
install_nginx() {
    log "Installation et configuration de Nginx..."
    
    apt install -y nginx
    
    # Configuration Nginx
    cat > /etc/nginx/sites-available/virtual-lab-manager << EOF
server {
    listen 80;
    server_name localhost;
    
    # Frontend
    location / {
        root $INSTALL_DIR/frontend/virtual-lab-frontend/dist;
        try_files \$uri \$uri/ /index.html;
    }
    
    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # WebSocket pour SSH/VNC
    location /api/v1/ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Activer le site
    ln -sf /etc/nginx/sites-available/virtual-lab-manager /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Tester la configuration
    nginx -t
    
    # Démarrer et activer Nginx
    systemctl start nginx
    systemctl enable nginx
    
    log "Nginx configuré et démarré"
}

# Configuration du firewall
configure_firewall() {
    log "Configuration du firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw --force enable
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 5900:5999/tcp  # Ports VNC
        ufw allow 22000:22999/tcp  # Ports SSH des VMs
        log "Firewall UFW configuré"
    else
        warn "UFW non disponible, configuration manuelle du firewall recommandée"
    fi
}

# Démarrage des services
start_services() {
    log "Démarrage des services..."
    
    # Initialiser la base de données
    cd $INSTALL_DIR/backend
    sudo -u $SERVICE_USER ./venv/bin/python -c "
from database import engine, Base
Base.metadata.create_all(bind=engine)
print('Base de données initialisée')
"
    
    # Démarrer les services
    systemctl start vlm-backend
    systemctl enable vlm-backend
    
    # Attendre que le backend soit prêt
    sleep 5
    
    systemctl start vlm-frontend
    systemctl enable vlm-frontend
    
    log "Services démarrés et activés"
}

# Affichage des informations finales
show_info() {
    log "Installation terminée avec succès!"
    echo
    echo -e "${BLUE}=== Informations de connexion ===${NC}"
    echo -e "URL de l'application: ${GREEN}http://$(hostname -I | awk '{print $1}')${NC}"
    echo -e "Base de données: ${GREEN}$DB_NAME${NC}"
    echo -e "Utilisateur DB: ${GREEN}$DB_USER${NC}"
    echo -e "Mot de passe DB: ${GREEN}$DB_PASSWORD${NC}"
    echo
    echo -e "${BLUE}=== Commandes utiles ===${NC}"
    echo -e "Statut des services: ${GREEN}systemctl status vlm-backend vlm-frontend${NC}"
    echo -e "Logs backend: ${GREEN}journalctl -u vlm-backend -f${NC}"
    echo -e "Logs frontend: ${GREEN}journalctl -u vlm-frontend -f${NC}"
    echo -e "Redémarrer: ${GREEN}systemctl restart vlm-backend vlm-frontend${NC}"
    echo
    echo -e "${YELLOW}Note: Sauvegardez le mot de passe de la base de données!${NC}"
}

# Fonction principale
main() {
    log "Début de l'installation de Virtual Lab Manager"
    
    check_root
    check_debian
    update_system
    install_python
    install_nodejs
    install_postgresql
    install_terraform
    install_ansible
    install_virtualization
    install_novnc
    create_user
    install_application
    configure_environment
    create_services
    install_nginx
    configure_firewall
    start_services
    show_info
    
    log "Installation complète!"
}

# Gestion des erreurs
trap 'error "Installation interrompue"' ERR

# Exécution
main "$@"

