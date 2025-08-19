#!/bin/bash

# Script de sauvegarde pour Virtual Lab Manager
# Sauvegarde la base de données et les configurations

set -e

# Variables
BACKUP_DIR="/opt/backups/virtual-lab-manager"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="virtual_lab_manager"
DB_USER="vlm_user"
INSTALL_DIR="/opt/virtual-lab-manager"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"

log "Début de la sauvegarde - $DATE"

# Sauvegarde de la base de données
log "Sauvegarde de la base de données..."
sudo -u postgres pg_dump "$DB_NAME" > "$BACKUP_DIR/database_$DATE.sql"

# Sauvegarde des configurations
log "Sauvegarde des configurations..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    "$INSTALL_DIR/.env" \
    "/etc/systemd/system/vlm-*.service" \
    "/etc/nginx/sites-available/virtual-lab-manager" \
    2>/dev/null || true

# Sauvegarde des logs Terraform/Ansible (si présents)
if [ -d "/tmp/terraform_lab_*" ] || [ -d "/tmp/ansible_lab_*" ]; then
    log "Sauvegarde des logs de déploiement..."
    tar -czf "$BACKUP_DIR/deployment_logs_$DATE.tar.gz" \
        /tmp/terraform_lab_* /tmp/ansible_lab_* \
        2>/dev/null || true
fi

# Nettoyage des anciennes sauvegardes (garder 7 jours)
log "Nettoyage des anciennes sauvegardes..."
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

log "Sauvegarde terminée: $BACKUP_DIR"
ls -la "$BACKUP_DIR" | tail -5

