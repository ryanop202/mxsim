#!/usr/bin/env python3
"""Extrait une ou plusieurs archives MX Simulator .saf dans un dossier.

Format .saf (vérifié sur sx2026r01anaheim1 / r03anaheim2 / r04houston) :
  - en-tête texte : une ligne par fichier "<taille_en_octets> <chemin>"
  - une ligne "-" termine l'en-tête
  - puis le contenu brut des fichiers, concaténés dans l'ordre de l'en-tête

Usage :  python3 tools/extract_saf.py refs/rf/*.saf --out refs/rf/extracted
Chaque .saf donne  <out>/<nom_de_piste>/ (terrain.png, tilemap, tileinfo, textures/, stadiums/ ...).
"""
import argparse, os, re, sys

def extract(saf, out):
    n = 0
    with open(saf, "rb") as f:
        entries = []
        while True:
            line = f.readline()
            m = re.match(rb"^(\d+) (\S.*?)\r?\n$", line)
            if not m:
                if line.strip() != b"-":
                    sys.exit(f"{saf}: en-tête inattendu: {line[:60]!r}")
                break
            entries.append((int(m.group(1)), m.group(2).decode("utf-8", "replace")))
        for size, rel in entries:
            data = f.read(size)
            if len(data) != size:
                sys.exit(f"{saf}: fichier tronqué à {rel}")
            dest = os.path.normpath(os.path.join(out, rel))
            if not dest.startswith(os.path.abspath(out) + os.sep) and not os.path.abspath(dest).startswith(os.path.abspath(out) + os.sep):
                sys.exit(f"chemin suspect refusé: {rel}")
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as g:
                g.write(data)
            n += 1
        rest = f.read()
    print(f"{os.path.basename(saf)}: {n} fichiers extraits" + (f" (+{len(rest)} octets inattendus en fin)" if rest else ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("saf", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for s in a.saf:
        extract(s, a.out)
