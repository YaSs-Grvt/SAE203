#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
config.py simplifié avec ipaddress :
Gestion du fichier YAML de configuration
"""

import sys
import os
import yaml
from ipaddress import IPv4Address, IPv4Network


def load_config(filename, create):
    """
    Charge le fichier YAML de configuration
    Si le fichier n'existe pas et create=True, crée un fichier minimal
    """
    # Vérifier si le fichier existe
    if os.path.exists(filename):
        # Le fichier existe, on le lit
        try:
            with open(filename, 'r') as f:
                cfg = yaml.safe_load(f)
            
            # Si le fichier est vide, retourner un dict vide
            if cfg is None:
                cfg = {}
            
            return cfg
            
        except Exception as e:
            print(f"Error: cannot parse configuration file {filename}: {e}", file=sys.stderr)
            sys.exit(1)
    
    else:
        # Le fichier n'existe pas
        if create:
            # Créer un fichier minimal
            minimal_cfg = {
                "dhcp_hosts_cfg": "/etc/dnsmasq.d/hosts.conf",
                "user": "sae203"
            }
            
            try:
                with open(filename, 'w') as f:
                    yaml.dump(minimal_cfg, f)
                return minimal_cfg
                
            except Exception as e:
                print(f"Error: cannot create configuration file {filename}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # Pas de création demandée
            print(f"Error: Configuration file {filename} not found.", file=sys.stderr)
            sys.exit(1)


def get_dhcp_server(ip_or_network, cfg):
    """
    Recherche le serveur DHCP qui gère une IP ou un réseau donné
    Retourne (server_ip, network_str) ou None si pas trouvé
    """
    # Récupérer la liste des serveurs DHCP
    servers = cfg.get("dhcp-servers", {})
    
    # Si aucun serveur configuré
    if not servers:
        return None
    
    # Parcourir tous les serveurs
    for server_ip, network_str in servers.items():
        # Cas 1 : correspondance exacte de réseau
        # Ex: on cherche "10.20.1.0/24" et c'est exactement ça dans la config
        if network_str == ip_or_network:
            return (server_ip, network_str)
        
        # Cas 2 : on a une IP et on cherche son réseau
        try:
            # Essayer de parser comme une adresse IP
            ip = IPv4Address(ip_or_network)
            
            # Parser le réseau du serveur
            network = IPv4Network(network_str)
            
            # Vérifier si l'IP appartient à ce réseau
            if ip in network:
                return (server_ip, network_str)
                
        except:
            # Ce n'était pas une IP valide ou un réseau valide
            # On continue avec le serveur suivant
            continue
    
    # Aucun serveur trouvé pour cette IP/réseau
    return None
