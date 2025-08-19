# Plan d'intégration Terraform, Ansible, QEMU/KVM/libvirt

## 1. Provisionnement des VMs avec Terraform et libvirt
- Le backend FastAPI générera dynamiquement des fichiers `.tf` basés sur la configuration du lab (nombre de VMs, CPU, RAM, disque, OS).
- Terraform utilisera le provider `libvirt` pour interagir avec QEMU/KVM via `libvirtd`.
- Les images OS (qcow2) seront pré-téléchargées ou créées à la volée par Terraform.
- Terraform sera exécuté en tant que sous-processus depuis le backend, capturant ses logs en temps réel.
- Les informations de connexion (IP, ports SSH/VNC) seront extraites de l'état Terraform (`terraform output`) et stockées dans la base de données.

## 2. Configuration logicielle avec Ansible
- Une fois les VMs provisionnées par Terraform, le backend déclenchera l'exécution d'Ansible.
- Le backend générera un inventaire Ansible dynamique basé sur les VMs créées et leurs adresses IP.
- Le fichier YAML d'Ansible fourni par l'utilisateur (décrivant les rôles logiciels) sera utilisé pour configurer les VMs.
- Ansible sera exécuté en tant que sous-processus depuis le backend, capturant ses logs en temps réel.
- Les logs d'Ansible seront également stockés et diffusés au frontend.

## 3. Gestion de l'état des VMs (Start/Stop/Restart)
- Le backend utilisera des commandes `virsh` (via une bibliothèque Python comme `python-libvirt` ou en exécutant des commandes shell) pour gérer l'état des VMs.
- Les actions (start, stop, restart) seront mappées aux commandes `virsh` correspondantes.
- L'état des VMs sera mis à jour dans la base de données en fonction des retours de `virsh`.

## 4. Persistance
- L'état de Terraform (`terraform.tfstate`) sera stocké dans la base de données pour chaque lab, permettant de reprendre les opérations ou de détruire l'infrastructure.
- Les disques des VMs seront persistants par défaut, gérés par libvirt.

## 5. Accès SSH/VNC
- Les ports SSH et VNC seront alloués dynamiquement et stockés dans la base de données.
- Le backend agira comme un proxy pour les connexions SSH (via `xterm.js` et un websocket) et VNC (via `noVNC` et un websocket).


