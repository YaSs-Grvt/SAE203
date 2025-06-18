#!/bin/bash

#Cela permet d'ajouter un filtre ssh pour interdire toute commande non autoriser


# Vérifier que SSH_ORIGINAL_COMMAND est défini
if [ -z "$SSH_ORIGINAL_COMMAND" ]; then
    echo "ERREUR: Aucune commande spécifiée"
    exit 1
fi

# Analyser la commande demandée
case "$SSH_ORIGINAL_COMMAND" in
    # Lire le fichier de configuration DHCP
    "cat /etc/dnsmasq.d/hosts.conf")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Redémarrer le service DHCP
    "sudo systemctl restart dnsmasq")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Recharger le service DHCP
    "sudo systemctl reload dnsmasq")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Vérifier le statut du service
    "systemctl status dnsmasq")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Chercher dans le fichier de config (grep avec paramètres)
    grep\ *\ /etc/dnsmasq.d/hosts.conf)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Ajouter une ligne au fichier (echo avec redirection)
    echo\ *\ \>\>\ /etc/dnsmasq.d/hosts.conf)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Supprimer/modifier une ligne du fichier (sed)
    sed\ -i*\ /etc/dnsmasq.d/hosts.conf)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Commandes de base autorisées
    "ls /etc/dnsmasq.d/")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    "test -f /etc/dnsmasq.d/hosts.conf")
        exec $SSH_ORIGINAL_COMMAND
        ;;
    
    # Toute autre commande = REFUSÉE
    *)
        echo "ERREUR: Commande non autorisée: $SSH_ORIGINAL_COMMAND" >&2
        exit 1
        ;;
esac
