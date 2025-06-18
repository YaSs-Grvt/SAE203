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

# 3. Importer config et dhcp
from config import load_config, get_dhcp_server
from dhcp   import dhcp_list

def print_usage():
    print("Usage: list-dhcp [serveur]")
    print("If no argument, lists all servers. Else, lists only for the given server.")
    sys.exit(1)

def main():
    # 4. Gérer l’argument optionnel
    target_arg = None
    if len(sys.argv) == 2:
        target_arg = sys.argv[1]
    elif len(sys.argv) > 2:
        print_usage()

    # 5. Charger le YAML
    config_path = join(PROJECT_DIR, "superviseur.yaml")
    try:
        cfg = load_config(config_path, create=False)
    except SystemExit:
        sys.exit(1)

    # 6. Construire la liste des serveurs à lister
    servers_to_list = []

    if target_arg:
        srv_info = get_dhcp_server(target_arg, cfg)
        if srv_info is None:
            if target_arg in cfg["dhcp-servers"]:
                servers_to_list.append(target_arg)
            else:
                print("cannot identify DHCP server", file=sys.stderr)
                sys.exit(1)
        else:
            servers_to_list.append(srv_info[0])
    else:
        servers_to_list = list(cfg["dhcp-servers"].keys())

    # 7. Demander la passphrase SSH une seule fois
    passphrase = getpass.getpass(prompt="Passphrase for SSH key (enter if none): ")
    key_file   = expanduser("~/.ssh/dhcp_superv_key")

    # 8. Pour chaque serveur, récupérer et afficher les réservations
    for srv in servers_to_list:
        print(f"{srv}:")
        try:
            entries = dhcp_list(server=srv, cfg=cfg, key_filename=key_file, passphrase=passphrase)
        except Exception as e:
            print(f"Error connecting to {srv}: {e}", file=sys.stderr)
            continue

        max_mac_len = max((len(e["mac"]) for e in entries), default=0)
        for e in entries:
            m = e["mac"]
            i = e["ip"]
            print(f"{m.ljust(max_mac_len)}    {i}")
        print()

if __name__ == "__main__":
    main()
