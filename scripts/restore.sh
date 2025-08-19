#!/bin/bash

# Script de restauration pour Virtual Lab Manager

set -e

# Variables
BACKUP_DIR="/opt/backups/virtual-lab-manager"
DB_NAME="virtual_lab_manager"
DB_USER="vlm_user"

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[RESTORE]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Vérifier les arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_date>"
    echo "Exemple: $0 20241219_143000"
    echo
    echo "Sauvegardes disponibles:"
    ls -1 "$BACKUP_DIR"/database_*.sql 2>/dev/null | sed 's/.*database_\(.*\)\.sql/\1/' || echo "Aucune sauvegarde trouvée"
    exit 1
fi

BACKUP_DATE="$1"
DB_BACKUP="$BACKUP_DIR/database_$BACKUP_DATE.sql"
CONFIG_BACKUP="$BACKUP_DIR/config_$BACKUP_DATE.tar.gz"

# Vérifier que les fichiers de sauvegarde existent
if [ ! -f "$DB_BACKUP" ]; then
    error "Sauvegarde de base de données non trouvée: $DB_BACKUP"
fi

log "Restauration à partir de la sauvegarde du $BACKUP_DATE"

# Arrêter les services
log "Arrêt des services..."
systemctl stop vlm-backend vlm-frontend 2>/dev/null || true

# Restaurer la base de données
log "Restauration de la base de données..."
warn "ATTENTION: Ceci va écraser la base de données actuelle!"
read -p "Continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    error "Restauration annulée"
fi

# Supprimer et recréer la base de données
sudo -u postgres dropdb "$DB_NAME" 2>/dev/null || true
sudo -u postgres createdb "$DB_NAME"
sudo -u postgres psql -d "$DB_NAME" < "$DB_BACKUP"

# Restaurer les configurations si disponibles
if [ -f "$CONFIG_BACKUP" ]; then
    log "Restauration des configurations..."
    tar -xzf "$CONFIG_BACKUP" -C / 2>/dev/null || warn "Erreur lors de la restauration des configurations"
    systemctl daemon-reload
fi

# Redémarrer les services
log "Redémarrage des services..."
systemctl start vlm-backend vlm-frontend
systemctl restart nginx

log "Restauration terminée avec succès!"
log "Vérifiez le statut des services: systemctl status vlm-backend vlm-frontend"

