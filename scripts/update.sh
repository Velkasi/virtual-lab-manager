#!/bin/bash

# Script de mise à jour pour Virtual Lab Manager

set -e

# Variables
INSTALL_DIR="/opt/virtual-lab-manager"
SERVICE_USER="vlm"
BACKUP_DIR="/opt/backups/virtual-lab-manager"
DATE=$(date +%Y%m%d_%H%M%S)

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[UPDATE]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Vérifier les privilèges root
if [[ $EUID -ne 0 ]]; then
    error "Ce script doit être exécuté en tant que root (sudo)"
fi

log "Début de la mise à jour - $DATE"

# Sauvegarde automatique avant mise à jour
log "Sauvegarde automatique avant mise à jour..."
if [ -f "$INSTALL_DIR/scripts/backup.sh" ]; then
    bash "$INSTALL_DIR/scripts/backup.sh"
else
    warn "Script de sauvegarde non trouvé, sauvegarde manuelle recommandée"
fi

# Arrêter les services
log "Arrêt des services..."
systemctl stop vlm-backend vlm-frontend

# Sauvegarder les configurations actuelles
log "Sauvegarde des configurations..."
cp "$INSTALL_DIR/.env" "$INSTALL_DIR/.env.backup.$DATE" 2>/dev/null || true

# Mise à jour du code (si dans un dépôt git)
if [ -d "$INSTALL_DIR/.git" ]; then
    log "Mise à jour du code depuis Git..."
    cd "$INSTALL_DIR"
    sudo -u $SERVICE_USER git pull
else
    warn "Pas de dépôt Git détecté, mise à jour manuelle du code nécessaire"
fi

# Mise à jour des dépendances Python
log "Mise à jour des dépendances Python..."
cd "$INSTALL_DIR/backend"
sudo -u $SERVICE_USER ./venv/bin/pip install --upgrade -r requirements.txt

# Mise à jour des dépendances Node.js
log "Mise à jour des dépendances Node.js..."
cd "$INSTALL_DIR/frontend/virtual-lab-frontend"
sudo -u $SERVICE_USER pnpm install
sudo -u $SERVICE_USER pnpm run build

# Migrations de base de données (si nécessaire)
log "Vérification des migrations de base de données..."
cd "$INSTALL_DIR/backend"
sudo -u $SERVICE_USER ./venv/bin/python -c "
from database import engine, Base
Base.metadata.create_all(bind=engine)
print('Schéma de base de données vérifié')
" || warn "Erreur lors de la vérification du schéma"

# Mise à jour des permissions
log "Mise à jour des permissions..."
chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/scripts/"*.sh

# Recharger la configuration systemd
systemctl daemon-reload

# Redémarrer les services
log "Redémarrage des services..."
systemctl start vlm-backend
sleep 5
systemctl start vlm-frontend
systemctl restart nginx

# Vérifier le statut des services
log "Vérification du statut des services..."
if systemctl is-active --quiet vlm-backend && systemctl is-active --quiet vlm-frontend; then
    log "Mise à jour terminée avec succès!"
    log "Services actifs et fonctionnels"
else
    error "Erreur: Un ou plusieurs services ne fonctionnent pas correctement"
fi

log "Vérifiez l'application: http://$(hostname -I | awk '{print $1}')"

