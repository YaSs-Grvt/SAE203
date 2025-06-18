#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check-dhcp.py simplifié :
Vérifie la cohérence des configurations DHCP (doublons MAC/IP)
"""

import sys
import os
import getpass

# === CONFIGURATION DU PATH PYTHON ===
# Même logique que add-dhcp-client.py pour trouver src/
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
src_dir = os.path.join(project_dir, "src")
sys.path.insert(0, src_dir)

# Import des modules
from config import load_config, get_dhcp_server
from dhcp import dhcp_list


def main():
    # === GESTION DE L'ARGUMENT OPTIONNEL ===
    # check-dhcp.py peut être appelé avec 0 ou 1 argument
    # 0 argument = vérifier tous les serveurs
    # 1 argument = vérifier un serveur/réseau spécifique
    
    target_server = None  # Par défaut, on vérifie tous les serveurs
    
    # len(sys.argv) = 1 si aucun argument (juste le nom du script)
    # len(sys.argv) = 2 si un argument
    if len(sys.argv) == 2:
        target_server = sys.argv[1]  # IP du serveur ou réseau (ex: "10.20.1.5" ou "10.20.1.0/24")
    elif len(sys.argv) > 2:
        print("Usage: check-dhcp.py [IP-OU-RESEAU]")
        print("Check DHCP configuration consistency")
        sys.exit(1)
    
    # === CHARGEMENT DE LA CONFIGURATION ===
    config_file = os.path.join(project_dir, "superviseur.yaml")
    try:
        cfg = load_config(config_file, create=False)
    except SystemExit:
        sys.exit(1)
    
    # === CONSTRUCTION DE LA LISTE DES SERVEURS À VÉRIFIER ===
    servers_to_check = []
    
    if target_server:
        # Un serveur spécifique a été demandé
        # On essaie de le trouver dans la config
        server_info = get_dhcp_server(target_server, cfg)
        if server_info is None:
            print("cannot identify DHCP server", file=sys.stderr)
            sys.exit(1)
        # server_info[0] contient l'IP du serveur
        servers_to_check.append(server_info[0])
    else:
        # Aucun serveur spécifié = vérifier tous les serveurs
        # cfg["dhcp-servers"] est un dictionnaire {ip_serveur: réseau}
        # .keys() donne juste les IPs des serveurs
        servers_to_check = list(cfg["dhcp-servers"].keys())
    
    # === AUTHENTIFICATION SSH (une seule fois) ===
    passphrase = getpass.getpass("SSH key passphrase (press Enter if none): ")
    if passphrase == "":
        passphrase = None
    key_file = os.path.expanduser("~/.ssh/dhcp_superv_key")
    
    # === VÉRIFICATION DE CHAQUE SERVEUR ===
    for server_ip in servers_to_check:
        print(f"\nChecking server: {server_ip}")
        
        try:
            # Récupérer la liste des réservations DHCP sur ce serveur
            # dhcp_list retourne une liste de dictionnaires [{"mac": "...", "ip": "..."}, ...]
            hosts = dhcp_list(
                server=server_ip,
                cfg=cfg,
                key_filename=key_file,
                passphrase=passphrase
            )
        except Exception as e:
            print(f"Error connecting to {server_ip}: {e}", file=sys.stderr)
            continue  # Passer au serveur suivant
        
        # === ANALYSE DES DOUBLONS ===
        # On va créer deux dictionnaires pour détecter les doublons
        
        # Dictionnaire pour compter les MACs
        # {mac: [liste des IPs associées]}
        mac_to_ips = {}
        
        # Dictionnaire pour compter les IPs
        # {ip: [liste des MACs associées]}
        ip_to_macs = {}
        
        # Remplir les dictionnaires
        for entry in hosts:
            mac = entry["mac"]
            ip = entry["ip"]
            
            # Pour chaque MAC, ajouter l'IP à sa liste
            # setdefault crée une liste vide si la clé n'existe pas
            if mac not in mac_to_ips:
                mac_to_ips[mac] = []
            mac_to_ips[mac].append(ip)
            
            # Pour chaque IP, ajouter la MAC à sa liste
            if ip not in ip_to_macs:
                ip_to_macs[ip] = []
            ip_to_macs[ip].append(mac)
        
        # === AFFICHAGE DES DOUBLONS MAC ===
        # Une MAC est en doublon si elle a plus d'une IP
        found_dup_mac = False
        for mac, ip_list in mac_to_ips.items():
            if len(ip_list) > 1:  # Plus d'une IP pour cette MAC
                if not found_dup_mac:
                    print("duplicate MAC addresses:")
                    found_dup_mac = True
                # Afficher toutes les lignes concernées
                for ip in ip_list:
                    print(f"dhcp-host={mac},{ip}")
        
        if not found_dup_mac:
            print("No duplicate MAC addresses.")
        
        # === AFFICHAGE DES DOUBLONS IP ===
        # Une IP est en doublon si elle a plus d'une MAC
        found_dup_ip = False
        for ip, mac_list in ip_to_macs.items():
            if len(mac_list) > 1:  # Plus d'une MAC pour cette IP
                if not found_dup_ip:
                    print("duplicate IP addresses:")
                    found_dup_ip = True
                # Afficher toutes les lignes concernées
                for mac in mac_list:
                    print(f"dhcp-host={mac},{ip}")
        
        if not found_dup_ip:
            print("No duplicate IP addresses.")


if __name__ == "__main__":
    main()
