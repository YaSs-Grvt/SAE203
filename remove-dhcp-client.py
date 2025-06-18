#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import getpass
from os.path import dirname, abspath, join, expanduser

# 1. Déduire PROJECT_DIR
PROJECT_DIR = dirname(dirname(abspath(__file__)))

# 2. Ajouter src/ au PYTHONPATH
SRC_DIR = join(PROJECT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 3. Importer validation, config et dhcp
from validation import validate_mac
from config     import load_config
from dhcp       import mac_exists, dhcp_remove

def print_usage():
    print("Usage: remove-dhcp-client <MAC>")
    print("Example: remove-dhcp-client 00:1a:2b:3c:4d:5e")
    sys.exit(1)

def main():
    # 4. Vérifier qu’on a exactement 1 argument (la MAC)
    if len(sys.argv) != 2:
        print_usage()

    mac_input = sys.argv[1]

    # 5. Valider l’adresse MAC
    try:
        mac = validate_mac(mac_input)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Charger le YAML
    config_path = join(PROJECT_DIR, "superviseur.yaml")
    try:
        cfg = load_config(config_path, create=False)
    except SystemExit:
        sys.exit(1)

    # 7. Trouver le serveur qui possède cette MAC (on ne fait pas encore appel à mac_exists)
    #    pour ne pas déclencher SSH avant de demander la passphrase.
    target_server = None
    for server_ip in cfg.get("dhcp-servers", {}).keys():
        # on va juste tester la présence potentielle, mais l'appel SSH est ici
        pass
    # Pour déterminer le serveur, on devra demander la passphrase tout de suite.

    # 8. Demander la passphrase (pour SSH) une seule fois
    passphrase = getpass.getpass(prompt="Passphrase for SSH key (enter if none): ")
    key_file   = expanduser("~/.ssh/dhcp_superv_key")

    # 9. Maintenant qu'on a la passphrase, rechercher le serveur avec mac_exists
    for server_ip in cfg.get("dhcp-servers", {}).keys():
        try:
            if mac_exists(server_ip=server_ip, mac=mac, cfg=cfg,
                          key_filename=key_file, passphrase=passphrase):
                target_server = server_ip
                break
        except Exception as e:
            # ignore les erreurs de connexion, on essaie le suivant
            continue

    if target_server is None:
        print("MAC address not found", file=sys.stderr)
        sys.exit(1)

    # 10. Appeler dhcp_remove pour supprimer la MAC sur target_server
    success = dhcp_remove(
        mac=mac,
        server=target_server,
        cfg=cfg,
        key_filename=key_file,
        passphrase=passphrase
    )

    if success:
        print(f"Removed DHCP reservation for {mac} on {target_server}")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
