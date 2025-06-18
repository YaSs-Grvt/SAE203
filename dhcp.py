#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
dhcp.py simplifié : 
Gestion des serveurs DHCP via SSH avec une approche plus directe
"""

import sys
from fabric import Connection
from paramiko import RSAKey
from paramiko.ssh_exception import SSHException, NoValidConnectionsError


def ip_other_mac_exists(server_ip, ip, mac, cfg, key_filename=None, passphrase=None):
    """
    Vérifie si l'IP est déjà utilisée par une autre MAC
    """
    # Préparation de la connexion SSH
    user = cfg["user"]
    connect_kwargs = {}
    
    # Chargement de la clé RSA si fournie
    if key_filename:
        try:
            if passphrase:
                pkey = RSAKey.from_private_key_file(key_filename, password=passphrase)
            else:
                pkey = RSAKey.from_private_key_file(key_filename)
            connect_kwargs["pkey"] = pkey
        except SSHException as e:
            print(f"Erreur clé RSA: {e}", file=sys.stderr)
            return False
    
    # Connexion et vérification
    try:
        conn = Connection(host=server_ip, user=user, connect_kwargs=connect_kwargs)
        
        # Récupérer le chemin du fichier depuis la config
        dhcp_file = cfg.get("dhcp_hosts_cfg", "/etc/dnsmasq.d/hosts.conf")
        
        # Lire toutes les lignes dhcp-host
        cmd = f"grep '^dhcp-host=' {dhcp_file} || true"
        result = conn.run(cmd, hide=True, warn=True)
        
        # Parcourir les lignes pour chercher des conflits
        for line in result.stdout.splitlines():
            if line.startswith("dhcp-host="):
                # Extraire MAC et IP de la ligne
                parts = line.replace("dhcp-host=", "").split(",")
                if len(parts) == 2:
                    existing_mac = parts[0].strip().lower()
                    existing_ip = parts[1].strip()
                    
                    # Si même IP mais MAC différente = conflit
                    if existing_ip == ip and existing_mac != mac.lower():
                        conn.close()
                        return True
        
        conn.close()
        return False
        
    except Exception as e:
        print(f"Erreur connexion: {e}", file=sys.stderr)
        return False


def mac_exists(server_ip, mac, cfg, key_filename=None, passphrase=None):
    """
    Vérifie si la MAC existe déjà dans la config
    """
    # Préparation connexion
    user = cfg["user"]
    connect_kwargs = {}
    
    if key_filename:
        try:
            if passphrase:
                pkey = RSAKey.from_private_key_file(key_filename, password=passphrase)
            else:
                pkey = RSAKey.from_private_key_file(key_filename)
            connect_kwargs["pkey"] = pkey
        except SSHException as e:
            print(f"Erreur clé RSA: {e}", file=sys.stderr)
            return False
    
    # Connexion et recherche
    try:
        conn = Connection(host=server_ip, user=user, connect_kwargs=connect_kwargs)
        
        # Récupérer le chemin du fichier
        dhcp_file = cfg.get("dhcp_hosts_cfg", "/etc/dnsmasq.d/hosts.conf")
        
        # Chercher la MAC (insensible à la casse)
        mac_lower = mac.lower()
        cmd = f"grep -i '^dhcp-host={mac_lower},' {dhcp_file} || true"
        result = conn.run(cmd, hide=True, warn=True)
        
        # Si on trouve quelque chose, la MAC existe
        exists = bool(result.stdout.strip())
        
        conn.close()
        return exists
        
    except Exception as e:
        print(f"Erreur connexion: {e}", file=sys.stderr)
        return False


def dhcp_add(ip, mac, server, cfg, key_filename=None, passphrase=None):
    """
    Ajoute ou met à jour une réservation DHCP
    """
    # Normaliser la MAC en minuscules
    mac_lower = mac.lower()
    
    # Vérifier d'abord si l'IP est déjà utilisée par une autre MAC
    if ip_other_mac_exists(server, ip, mac_lower, cfg, key_filename, passphrase):
        print("error: IP address already in use.", file=sys.stderr)
        return False
    
    # Préparation connexion
    user = cfg["user"]
    connect_kwargs = {}
    
    if key_filename:
        try:
            if passphrase:
                pkey = RSAKey.from_private_key_file(key_filename, password=passphrase)
            else:
                pkey = RSAKey.from_private_key_file(key_filename)
            connect_kwargs["pkey"] = pkey
        except SSHException as e:
            print(f"Erreur clé RSA: {e}", file=sys.stderr)
            return False
    
    # Connexion et modification
    try:
        conn = Connection(host=server, user=user, connect_kwargs=connect_kwargs)
        
        # Récupérer le chemin du fichier
        dhcp_file = cfg.get("dhcp_hosts_cfg", "/etc/dnsmasq.d/hosts.conf")
        
        # Vérifier si la MAC existe déjà
        if mac_exists(server, mac_lower, cfg, key_filename, passphrase):
            # La MAC existe, on la remplace avec sed
            sed_cmd = f"sudo sed -i 's|^dhcp-host={mac_lower},.*$|dhcp-host={mac_lower},{ip}|' {dhcp_file}"
            result = conn.run(sed_cmd, hide=False, warn=True)
            
            if result.exited != 0:
                print(f"error: Erreur lors de la mise à jour de {mac_lower}", file=sys.stderr)
                conn.close()
                return False
        else:
            # La MAC n'existe pas, on l'ajoute
            echo_cmd = f"echo 'dhcp-host={mac_lower},{ip}' | sudo tee -a {dhcp_file}"
            result = conn.run(echo_cmd, hide=False, warn=True)
            
            if result.exited != 0:
                print(f"error: Erreur lors de l'ajout de {mac_lower}", file=sys.stderr)
                conn.close()
                return False
        
        # Redémarrer dnsmasq
        result = conn.run("sudo systemctl restart dnsmasq", hide=False, warn=True)
        if result.exited != 0:
            print(f"error: Impossible de redémarrer dnsmasq", file=sys.stderr)
            conn.close()
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur connexion: {e}", file=sys.stderr)
        return False


def dhcp_remove(mac, server, cfg, key_filename=None, passphrase=None):
    """
    Supprime une réservation DHCP
    """
    mac_lower = mac.lower()
    
    # Vérifier d'abord si la MAC existe
    if not mac_exists(server, mac_lower, cfg, key_filename, passphrase):
        print("MAC address not found", file=sys.stderr)
        return False
    
    # Préparation connexion
    user = cfg["user"]
    connect_kwargs = {}
    
    if key_filename:
        try:
            if passphrase:
                pkey = RSAKey.from_private_key_file(key_filename, password=passphrase)
            else:
                pkey = RSAKey.from_private_key_file(key_filename)
            connect_kwargs["pkey"] = pkey
        except SSHException as e:
            print(f"Erreur clé RSA: {e}", file=sys.stderr)
            return False
    
    # Connexion et suppression
    try:
        conn = Connection(host=server, user=user, connect_kwargs=connect_kwargs)
        
        # Récupérer le chemin du fichier
        dhcp_file = cfg.get("dhcp_hosts_cfg", "/etc/dnsmasq.d/hosts.conf")
        
        # Supprimer la ligne avec sed
        sed_cmd = f"sudo sed -i '/^dhcp-host={mac_lower},/d' {dhcp_file}"
        result = conn.run(sed_cmd, hide=False, warn=True)
        
        if result.exited != 0:
            print(f"error: Erreur lors de la suppression de {mac_lower}", file=sys.stderr)
            conn.close()
            return False
        
        # Redémarrer dnsmasq
        result = conn.run("sudo systemctl restart dnsmasq", hide=False, warn=True)
        if result.exited != 0:
            print(f"error: Impossible de redémarrer dnsmasq", file=sys.stderr)
            conn.close()
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Erreur connexion: {e}", file=sys.stderr)
        return False


def dhcp_list(server, cfg, key_filename=None, passphrase=None):
    """
    Liste toutes les réservations DHCP d'un serveur
    """
    # Préparation connexion
    user = cfg["user"]
    connect_kwargs = {}
    
    if key_filename:
        try:
            if passphrase:
                pkey = RSAKey.from_private_key_file(key_filename, password=passphrase)
            else:
                pkey = RSAKey.from_private_key_file(key_filename)
            connect_kwargs["pkey"] = pkey
        except SSHException as e:
            print(f"Erreur clé RSA: {e}", file=sys.stderr)
            return []
    
    # Connexion et lecture
    try:
        conn = Connection(host=server, user=user, connect_kwargs=connect_kwargs)
        
        # Récupérer le chemin du fichier
        dhcp_file = cfg.get("dhcp_hosts_cfg", "/etc/dnsmasq.d/hosts.conf")
        
        # Lire toutes les lignes dhcp-host
        cmd = f"grep '^dhcp-host=' {dhcp_file} || true"
        result = conn.run(cmd, hide=True, warn=True)
        
        # Construire la liste des entrées
        entries = []
        for line in result.stdout.splitlines():
            if line.startswith("dhcp-host="):
                # Extraire MAC et IP
                parts = line.replace("dhcp-host=", "").split(",")
                if len(parts) == 2:
                    mac_addr = parts[0].strip().lower()
                    ip_addr = parts[1].strip()
                    
                    # Ajouter à la liste
                    entries.append({
                        "mac": mac_addr,
                        "ip": ip_addr
                    })
        
        conn.close()
        return entries
        
    except Exception as e:
        print(f"Erreur connexion: {e}", file=sys.stderr)
        return []
