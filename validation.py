#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
validation.py simplifié :
Validation des adresses MAC et IP
"""

from ipaddress import IPv4Address


def validate_mac(mac_str):
    """
    Vérifie que l'adresse MAC est valide (format xx:xx:xx:xx:xx:xx)
    Retourne la MAC en minuscules si valide, sinon lève ValueError
    """
    # Convertir en minuscules
    mac = mac_str.lower()
    
    # Séparer les parties
    parts = mac.split(':')
    
    # Vérifier qu'on a exactement 6 parties
    if len(parts) != 6:
        raise ValueError("bad MAC address")
    
    # Vérifier chaque partie
    for part in parts:
        # Chaque partie doit avoir exactement 2 caractères
        if len(part) != 2:
            raise ValueError("bad MAC address")
        
        # Vérifier que ce sont des caractères hexadécimaux
        for char in part:
            if char not in '0123456789abcdef':
                raise ValueError("bad MAC address")
    
    return mac


def validate_ip(ip_str):
    """
    Vérifie que l'IP est valide et utilisable pour DHCP
    Retourne l'IP si valide, sinon lève ValueError
    """
    try:
        # Parser l'adresse IP
        ip = IPv4Address(ip_str)
        
        # Vérifier que ce n'est pas une adresse spéciale
        if (ip.is_multicast or      # 224.0.0.0 - 239.255.255.255
            ip.is_unspecified or    # 0.0.0.0
            ip.is_reserved or       # Réservée IETF
            ip.is_loopback or       # 127.0.0.0/8
            ip.is_link_local):      # 169.254.0.0/16
            raise ValueError("bad IP address")
        
        # L'IP est valide
        return ip_str
        
    except:
        # Erreur de parsing ou IP invalide
        raise ValueError("bad IP address")
