#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

import toml

# Lese die pyproject.toml Datei
with open("pyproject.toml", "r") as file:
    pyproject = toml.load(file)

    # Extrahiere direkte Abhängigkeiten
    dependencies = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
    dev_dependencies = (
        pyproject.get("tool").get("poetry").get("group").get("dev", {}).get("dependencies", {})
    )

    # Kombiniere alle Abhängigkeiten
    direct_dependencies = set(dependencies.keys()).union(set(dev_dependencies.keys()))

    # Führe den Befehl 'poetry show --outdated' aus und speichere die Ausgabe
    result = subprocess.run(["poetry", "show", "--outdated"], capture_output=True, text=True)

    # Filtere nur die Pakete, die in den direkten Abhängigkeiten stehen
    outdated_packages = result.stdout.splitlines()
    filtered_outdated = [
        line for line in outdated_packages if line.split()[0] in direct_dependencies
    ]

    # Ausgabe der veralteten direkten Abhängigkeiten
    print("Veraltete direkte Abhängigkeiten:")
    for package in filtered_outdated:
        print(package)
