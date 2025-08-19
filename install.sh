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

    if ! command -v python3 &> /dev/null; then
        ln -sf /usr/bin/python3.11 /usr/bin/python3
    fi
}

# Installation de Node.js
install_nodejs() {
    log "Installation de Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt install -y nodejs
    npm install -g pnpm
    log "Node.js $(node --version) et pnpm installés"
}

# Installation de PostgreSQL
install_postgresql() {
    log "Installation de PostgreSQL..."
    apt install -y postgresql postgresql-contrib
    systemctl start postgresql
    systemctl enable postgresql

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
    usermod -aG libvirt $SERVICE_USER 2>/dev/null || true
    systemctl start libvirtd
    systemctl enable libvirtd

    if ! virt-host-validate qemu >/dev/null 2>&1; then
        warn "La virtualisation matérielle pourrait ne pas être disponible"
    fi
    log "Virtualisation QEMU/KVM configurée"
}

# Installer les dépendances pour libvirt-python
install_libvirt_python_dependencies() {
    log "Installation des dépendances pour libvirt-python..."
    apt install -y pkg-config libvirt-dev python3-dev build-essential
}

# Installation de noVNC
install_novnc() {
    log "Installation de noVNC..."
    apt install -y novnc websockify
    mkdir -p /opt/novnc
    if [ ! -d "/opt/novnc/noVNC" ]; then
        git clone https://github.com/novnc/noVNC.git /opt/novnc/noVNC
        git clone https://github.com/novnc/websockify.git /opt/novnc/websockify
    fi
    log "noVNC installé"
}

# Création de l'utilisateur système
create_user() {
    log "Création de l'utilisateur système $SERVICE_USER..."
    export PATH=$PATH:/usr/sbin:/sbin
    for grp in libvirt kvm; do
        if ! getent group $grp >/dev/null; then
            /usr/sbin/groupadd $grp
        fi
    done
    if ! id "$SERVICE_USER" &>/dev/null; then
        /usr/sbin/useradd -r -s /bin/bash -d /home/$SERVICE_USER -m $SERVICE_USER
        /usr/sbin/usermod -aG libvirt,kvm $SERVICE_USER
    fi
    mkdir -p /home/$SERVICE_USER/.ssh
    chown -R $SERVICE_USER:$SERVICE_USER /home/$SERVICE_USER
    log "Utilisateur $SERVICE_USER créé"
}

# Installation de l'application
install_application() {
    log "Installation de l'application Virtual Lab Manager..."
    mkdir -p $INSTALL_DIR
    cp -r . $INSTALL_DIR/
    chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

    log "Installation des dépendances Python..."
    cd $INSTALL_DIR/backend
    sudo -u $SERVICE_USER python3 -m venv venv
    sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade pip
    sudo -u $SERVICE_USER ./venv/bin/pip install -r requirements.txt

    log "Installation des dépendances Node.js..."
    cd $INSTALL_DIR/frontend/virtual-lab-frontend
    sudo -u $SERVICE_USER pnpm install

    log "Build du frontend..."
    sudo -u $SERVICE_USER pnpm run build
    log "Application installée dans $INSTALL_DIR"
}

# Reste du script inchangé...
