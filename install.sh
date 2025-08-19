#!/bin/bash

# Virtual Lab Manager - Script d'installation pour Debian 12
# Ce script installe et configure tous les composants nécessaires

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Variables de configuration
INSTALL_DIR="/opt/virtual-lab-manager"
SERVICE_USER="vlm"
DB_NAME="virtual_lab_manager"
DB_USER="vlm_user"
DB_PASSWORD=$(openssl rand -base64 32)

# Fonctions utilitaires
log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Vérifications
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root (sudo)"
    fi
}
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
    apt install -y curl wget gnupg2 software-properties-common apt-transport-https ca-certificates passwd git
}

# Installation de Python
install_python() {
    log "Installation de Python 3.11 et pip..."
    apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    if ! command -v python3 &>/dev/null; then
        ln -sf /usr/bin/python3.11 /usr/bin/python3
    fi
}

# Installation Node.js
install_nodejs() {
    log "Installation de Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
    npm install -g pnpm
    log "Node.js $(node --version) et pnpm installés"
}

# Installation PostgreSQL
install_postgresql() {
    log "Installation de PostgreSQL..."
    apt install -y postgresql postgresql-contrib
    systemctl enable --now postgresql

    log "Configuration de la base de données..."
    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER';" | grep -q 1 || \
        sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
}

# Installation Terraform
install_terraform() {
    log "Installation de Terraform..."
    wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
    apt update
    apt install -y terraform
}

# Installation Ansible
install_ansible() {
    log "Installation d'Ansible..."
    apt install -y ansible
}

# Installation Virtualisation
install_virtualization() {
    log "Installation de QEMU/KVM et libvirt..."
    apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager
    export PATH=$PATH:/usr/sbin:/sbin
    usermod -aG libvirt $SERVICE_USER 2>/dev/null || true
    systemctl enable --now libvirtd
}

# Dépendances libvirt-python
install_libvirt_python_dependencies() {
    log "Installation des dépendances pour libvirt-python..."
    apt install -y pkg-config libvirt-dev python3-dev build-essential
}

# Installation noVNC
install_novnc() {
    log "Installation de noVNC..."
    apt install -y novnc websockify
    mkdir -p /opt/novnc
    if [ ! -d "/opt/novnc/noVNC" ]; then
        git clone https://github.com/novnc/noVNC.git /opt/novnc/noVNC
        git clone https://github.com/novnc/websockify.git /opt/novnc/websockify
    fi
}

# Création utilisateur système
create_user() {
    log "Création de l'utilisateur $SERVICE_USER..."
    export PATH=$PATH:/usr/sbin:/sbin
    for grp in libvirt kvm; do
        getent group $grp >/dev/null || /usr/sbin/groupadd $grp
    done
    if ! id "$SERVICE_USER" &>/dev/null; then
        /usr/sbin/useradd -r -s /bin/bash -d /home/$SERVICE_USER -m $SERVICE_USER
        /usr/sbin/usermod -aG libvirt,kvm $SERVICE_USER
    fi
    mkdir -p /home/$SERVICE_USER/.ssh
    chown -R $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER
}

# Installation de l’application
install_application() {
    log "Installation de Virtual Lab Manager..."
    mkdir -p $INSTALL_DIR
    cp -r . $INSTALL_DIR/
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

    log "Backend Python..."
    cd $INSTALL_DIR/backend
    sudo -u $SERVICE_USER python3 -m venv venv
    sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

    log "Frontend Node.js..."
    cd $INSTALL_DIR/frontend/virtual-lab-frontend
    sudo -u $SERVICE_USER pnpm install
    sudo -u $SERVICE_USER pnpm run build
}

# Installation services
setup_services() {
    log "Configuration des services systemd..."
    cp $INSTALL_DIR/deploy/vlm-backend.service /etc/systemd/system/
    cp $INSTALL_DIR/deploy/vlm-frontend.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now vlm-backend
    systemctl enable --now vlm-frontend
}

# --------- MAIN ---------
check_root
check_debian
update_system
create_user
install_python
install_nodejs
install_postgresql
install_terraform
install_ansible
install_virtualization
install_libvirt_python_dependencies
install_novnc
install_application
setup_services

log "Installation terminée !"
echo -e "${BLUE}Accès via : http://localhost:3000${NC}"
echo -e "${YELLOW}DB User: $DB_USER / Password: $DB_PASSWORD${NC}"
