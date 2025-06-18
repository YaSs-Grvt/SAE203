#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Import des modules standards Python
import sys       # Pour accéder aux arguments de la ligne de commande et quitter le programme
import os        # Pour manipuler les chemins de fichiers
import getpass   # Pour demander un mot de passe sans l'afficher à l'écran

# === CONFIGURATION DU PATH PYTHON ===
# Python cherche les modules dans certains répertoires (le "path")
# On doit ajouter notre répertoire src/ pour qu'il trouve nos modules

# __file__ = chemin de ce script (ex: /home/sae203/.../bin/add-dhcp-client.py)
# os.path.abspath() transforme en chemin absolu complet
# os.path.dirname() enlève le nom du fichier pour garder juste le répertoire
script_dir = os.path.dirname(os.path.abspath(__file__))  # = /home/sae203/.../bin

# On remonte d'un niveau pour avoir le répertoire du projet
project_dir = os.path.dirname(script_dir)  # = /home/sae203/.../superviseur-dhcp-code

# On construit le chemin vers src/ en combinant project_dir + "src"
src_dir = os.path.join(project_dir, "src")  # = /home/sae203/.../superviseur-dhcp-code/src

# On ajoute src/ au début de la liste des chemins où Python cherche les modules
# Le 0 signifie "mettre en première position" pour priorité maximale
sys.path.insert(0, src_dir)

# Maintenant Python peut trouver nos modules dans src/
from validation import validate_mac, validate_ip       # Fonctions de validation MAC/IP
from config import load_config, get_dhcp_server       # Gestion du fichier YAML
from dhcp import dhcp_add                             # Fonction pour ajouter via SSH


def main():
    # === VÉRIFICATION DES ARGUMENTS ===
    # sys.argv contient les arguments : [nom_script, arg1, arg2, ...]
    # On veut exactement 3 éléments : script + MAC + IP
    if len(sys.argv) != 3:
        print("Usage: add-dhcp-client.py <MAC> <IP>")
        print("Example: add-dhcp-client.py 00:1a:2b:3c:4d:5e 10.20.1.60")
        sys.exit(1)  # Quitte le programme avec code d'erreur 1
    
    # sys.argv[0] = nom du script
    # sys.argv[1] = premier argument (MAC)
    # sys.argv[2] = deuxième argument (IP)
    mac_input = sys.argv[1]
    ip_input = sys.argv[2]
    
    # === VALIDATION DE L'ADRESSE MAC ===
    try:
        # validate_mac vérifie le format et retourne la MAC en minuscules
        mac = validate_mac(mac_input)
    except ValueError:
        # Si le format est invalide, validate_mac lève une ValueError
        # file=sys.stderr envoie le message sur la sortie d'erreur (pas la sortie standard)
        print("error: bad MAC address", file=sys.stderr)
        sys.exit(1)
    
    # === VALIDATION DE L'ADRESSE IP ===
    try:
        # validate_ip vérifie le format et les restrictions (pas multicast, etc.)
        ip = validate_ip(ip_input)
    except ValueError:
        print("error: bad IP address", file=sys.stderr)
        sys.exit(1)
    
    # === CHARGEMENT DU FICHIER DE CONFIGURATION ===
    # Construit le chemin complet vers superviseur.yaml
    config_file = os.path.join(project_dir, "superviseur.yaml")
    try:
        # load_config lit le fichier YAML et retourne un dictionnaire
        # create=False signifie "ne pas créer le fichier s'il n'existe pas"
        cfg = load_config(config_file, create=False)
    except SystemExit:
        # load_config fait déjà sys.exit() en cas d'erreur
        # donc on propage juste la sortie
        sys.exit(1)
    
    # === IDENTIFICATION DU SERVEUR DHCP ===
    # get_dhcp_server cherche quel serveur gère le réseau de cette IP
    # Retourne (ip_serveur, réseau) ou None si pas trouvé
    server_info = get_dhcp_server(ip, cfg)
    if server_info is None:
        print("Unable to identify DHCP server", file=sys.stderr)
        sys.exit(1)
    
    # server_info est un tuple : (ip_serveur, réseau)
    # On ne veut que l'IP du serveur (premier élément, index 0)
    server_ip = server_info[0]
    
    # === AUTHENTIFICATION SSH ===
    print("Connecting to DHCP server...")
    # getpass.getpass() demande un mot de passe sans l'afficher
    # L'utilisateur voit le prompt mais pas ce qu'il tape
    passphrase = getpass.getpass("SSH key passphrase (press Enter if none): ")
    
    # Si l'utilisateur appuie juste sur Entrée, passphrase est une chaîne vide ""
    # Dans ce cas, on met None (fabric comprend None = pas de passphrase)
    if passphrase == "":
        passphrase = None
    
    # os.path.expanduser("~") remplace ~ par le répertoire home de l'utilisateur
    # Ex: ~/.ssh/dhcp_superv_key devient /home/sae203/.ssh/dhcp_superv_key
    key_file = os.path.expanduser("~/.ssh/dhcp_superv_key")
    
    # === AJOUT DE LA RÉSERVATION DHCP ===
    print(f"Adding DHCP reservation on server {server_ip}...")
    
    # Appel de la fonction dhcp_add qui fait tout le travail :
    # - Se connecte en SSH au serveur
    # - Vérifie les conflits
    # - Ajoute ou met à jour la réservation
    # - Redémarre dnsmasq
    success = dhcp_add(
        ip=ip,                    # L'IP à réserver
        mac=mac,                  # La MAC qui aura cette IP
        server=server_ip,         # Le serveur DHCP à modifier
        cfg=cfg,                  # La configuration (contient l'utilisateur SSH, etc.)
        key_filename=key_file,    # Le fichier de clé privée SSH
        passphrase=passphrase     # La passphrase de la clé (ou None)
    )
    
    # === AFFICHAGE DU RÉSULTAT ===
    if success:
        # f-string : permet d'insérer des variables dans la chaîne avec {variable}
        print(f"Success: Added DHCP reservation {mac} → {ip} on server {server_ip}")
        sys.exit(0)  # Code 0 = succès
    else:
        # dhcp_add a déjà affiché le message d'erreur spécifique
        sys.exit(1)  # Code 1 = échec


# === POINT D'ENTRÉE DU PROGRAMME ===
# Cette condition est vraie seulement si le script est exécuté directement
# (pas s'il est importé comme module)
if __name__ == "__main__":
    main()  # Lance la fonction principale
