# Esquisse de l'interface utilisateur et des flux de travail

## Pages principales

### 1. Tableau de bord (Dashboard)
- Vue d'ensemble des laboratoires virtuels existants.
- Liste des labs avec leur nom, statut (déployé, en cours, erreur, etc.), nombre de VMs.
- Boutons d'action rapide (Déployer, Arrêter, Supprimer, Accéder).
- Bouton 


pour créer un nouveau lab.

### 2. Création de Lab
- Formulaire pour définir les propriétés du lab:
  - Nom du lab.
  - Description.
  - Section pour ajouter des VMs:
    - Bouton "Ajouter VM".
    - Pour chaque VM:
      - Nom de la VM.
      - Sélecteur de vCPU (ex: 1, 2, 4).
      - Sélecteur de RAM (ex: 1GB, 2GB, 4GB).
      - Sélecteur de disque (ex: 20GB, 50GB, 100GB).
      - Sélecteur d'image OS (liste déroulante).
      - Champ de texte pour tags.
  - Champ de texte pour coller le contenu YAML d'Ansible (optionnel).
- Bouton "Créer Lab".

### 3. Détails du Lab / Vue de déploiement
- Affichage du nom et du statut du lab.
- Liste des VMs du lab avec leur statut individuel.
- Section de logs en temps réel pour Terraform et Ansible (console textuelle).
- Barre de progression du déploiement.
- Boutons d'action pour le lab (Arrêter tout, Redémarrer tout, Supprimer).

### 4. Vue de la VM individuelle
- Nom de la VM, hardware, OS.
- Statut de la VM (Running, Stopped).
- Boutons d'action (Start, Stop, Restart).
- Boutons pour accéder à SSH et VNC:
  - Cliquer ouvre une nouvelle fenêtre/onglet ou un modal avec le client intégré (xterm.js pour SSH, noVNC pour VNC).

## Flux de travail

1. **Création d'un nouveau Lab**:
   - L'utilisateur navigue vers la page "Créer Lab".
   - Rempli le formulaire, ajoute les VMs et leurs configurations.
   - Soumet le formulaire.
   - Le backend reçoit la requête, crée l'entrée dans la DB et renvoie l'utilisateur vers la page de détails du lab.

2. **Déploiement d'un Lab**:
   - Sur la page de détails du lab, l'utilisateur clique sur "Déployer".
   - Le backend déclenche l'exécution de Terraform.
   - Les logs de Terraform sont streamés au frontend.
   - Une fois Terraform terminé, Ansible est exécuté.
   - Les logs d'Ansible sont streamés au frontend.
   - Le statut du lab et des VMs est mis à jour en temps réel.

3. **Accès SSH/VNC**:
   - Sur la page de détails du lab ou de la VM, l'utilisateur clique sur "SSH" ou "VNC".
   - Le frontend établit une connexion WebSocket avec le backend.
   - Le backend proxyfie la connexion vers la VM cible (via xterm.js ou noVNC).
   - La session est affichée dans le navigateur.

4. **Gestion de l'état des VMs**:
   - L'utilisateur clique sur Start/Stop/Restart pour une VM ou pour l'ensemble du lab.
   - Le backend exécute les commandes `virsh` appropriées.
   - Le statut de la VM est mis à jour dans la DB et reflété dans l'UI.


