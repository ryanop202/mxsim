"""Planches comparatives : photo de référence (gauche) / rendu de contrôle (droite).

  py -3.12 -I src/compare_views.py   -> renders/compare_<vue>.png pour chaque vue ayant un champ 'ref'
"""
import os
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
views = json.load(open(os.path.join(ROOT, "blender", "views.json"), encoding="utf8"))
H = 620
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\bahnschrift.ttf", 22)
except Exception:
    font = ImageFont.load_default()

for name, v in views.items():
    if "ref" not in v:
        continue
    rp = os.path.join(ROOT, "references", "originals", v["ref"])
    vp = os.path.join(ROOT, "renders", "view_%s.png" % name)
    if not (os.path.exists(rp) and os.path.exists(vp)):
        continue
    a = Image.open(rp).convert("RGB"); b = Image.open(vp).convert("RGB")
    a = a.resize((int(a.width * H / a.height), H)); b = b.resize((int(b.width * H / b.height), H))
    W = a.width + b.width + 30
    out = Image.new("RGB", (W, H + 44), (24, 24, 26))
    out.paste(a, (10, 34)); out.paste(b, (a.width + 20, 34))
    d = ImageDraw.Draw(out)
    d.text((12, 6), "Photo : " + v["ref"][:60], font=font, fill=(230, 230, 230))
    d.text((a.width + 22, 6), "Rendu : " + name, font=font, fill=(230, 230, 230))
    out.save(os.path.join(ROOT, "renders", "compare_%s.png" % name))
    print("compare_%s.png" % name)
