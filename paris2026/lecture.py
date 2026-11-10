"""Plan annoté + tableau du relevé Supercross Paris 2026 (lecture_photos.json).

  py -3.15 -I paris2026/lecture.py      -> paris2026/refs/plan_annote.png (local, dérivé du visuel) + tableau en console
Longueurs en ft = px x echelle_ft_par_px. Les hauteurs et profils viennent de l'unité JGSX choisie (lib/sx_units.json).
"""
import os
import json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(HERE, "lecture_photos.json"), encoding="utf-8"))
U = json.load(open(os.path.join(ROOT, "lib", "sx_units.json")))["units"]
S = D["echelle_ft_par_px"]
K = 2   # agrandissement du plan
COL = {"S": (0, 150, 255), "B": (255, 140, 0), "T": (220, 0, 120), "X": (200, 0, 0), "whoops": (0, 170, 90), "low": (120, 120, 120)}


def rows():
    out, n = [], 0
    for lane in D["tour"]:
        for o in lane.get("obstacles", []):
            n += 1
            a, b = o["px"]
            u = U.get(o["jgsx"], {})
            out.append(dict(n=n, lane=lane["id"], type=o["type"], L=abs(b - a) * S, ju=o["jgsx"],
                            jL=u.get("L"), jH=u.get("H"), note=o.get("note", ""), lane_d=lane, px=o["px"]))
    return out


def gaps(lane):
    obs = lane.get("obstacles", [])
    sgn = 1 if lane["sens"] in ("+x", "+y") else -1
    seq = sorted(obs, key=lambda o: sgn * o["px"][0])
    g = []
    for p, q in zip(seq, seq[1:]):
        e = max(p["px"]) if sgn > 0 else min(p["px"])
        s = min(q["px"]) if sgn > 0 else max(q["px"])
        g.append(abs(s - e) * S)
    return g


def draw(path_in, path_out):
    im = Image.open(path_in).convert("RGB")
    im = im.resize((im.size[0] * K, im.size[1] * K), Image.LANCZOS)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f = ImageFont.truetype("arialbd.ttf", 18); fs = ImageFont.truetype("arial.ttf", 14)
    for r in rows():
        lane = r["lane_d"]; a, b = sorted(r["px"]); y0, y1 = lane["pos"]
        if lane["axe"] == "y":
            box = (a * K, y0 * K, b * K, y1 * K)
        else:
            box = (y0 * K, a * K, y1 * K, b * K)
        c = COL.get(r["type"], (0, 0, 0))
        d.rectangle(box, outline=c + (255,), width=3, fill=c + (50,))
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=(255, 255, 255, 235), outline=c + (255,), width=2)
        d.text((cx, cy), str(r["n"]), font=f, fill=(0, 0, 0, 255), anchor="mm")
    for lane in D["tour"]:
        if "pos" not in lane:
            continue
        y0, y1 = lane["pos"]
        obs = lane.get("obstacles", [])
        xs = [p for o in obs for p in o["px"]] or lane.get("px", [0, 0])
        a, b = min(xs), max(xs)
        if lane["axe"] == "y":
            yc = (y0 + y1) / 2 * K; x0, x1 = (a * K, b * K) if lane["sens"] == "+x" else (b * K, a * K)
            P, Q = (x0, yc), (x1, yc); lab = (min(x0, x1) - 8, yc)
        else:
            xc = (y0 + y1) / 2 * K; z0, z1 = (a * K, b * K) if lane["sens"] == "+y" else (b * K, a * K)
            P, Q = (xc, z0), (xc, z1); lab = (xc, min(z0, z1) - 10)
        d.line([P, Q], fill=(220, 0, 0, 200), width=3)
        import math
        ang = math.atan2(Q[1] - P[1], Q[0] - P[0])
        for t in (0.25, 0.75):
            m = (P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t)
            h = [(m[0] + 14 * math.cos(ang), m[1] + 14 * math.sin(ang)),
                 (m[0] + 10 * math.cos(ang + 2.5), m[1] + 10 * math.sin(ang + 2.5)),
                 (m[0] + 10 * math.cos(ang - 2.5), m[1] + 10 * math.sin(ang - 2.5))]
            d.polygon(h, fill=(220, 0, 0, 255))
        d.text(lab, lane["id"], font=f, fill=(220, 0, 0, 255), anchor="rm" if lane["axe"] == "y" else "mb",
               stroke_width=3, stroke_fill=(255, 255, 255, 255))
    gx = D["depart"]["grilles_x"] * K
    d.line([(gx, 330 * K), (gx, 410 * K)], fill=(0, 0, 0, 255), width=5)
    d.text((gx - 6, 300 * K), "DÉPART (22 grilles)", font=f, fill=(0, 0, 0, 255), anchor="rm",
           stroke_width=3, stroke_fill=(255, 255, 255, 255))
    # échelle : 100 ft
    L = 100 / S * K
    d.rectangle([20, im.size[1] - 40, 20 + L, im.size[1] - 30], fill=(0, 0, 0, 255))
    d.text((20 + L + 8, im.size[1] - 35), "100 ft", font=f, fill=(0, 0, 0, 255), anchor="lm",
           stroke_width=3, stroke_fill=(255, 255, 255, 255))
    out = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    out.save(path_out, quality=92)


def table():
    print("| # | couloir | type | L lue (ft) | unité JGSX | L JGSX (ft) | H JGSX (ft) | note |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows():
        print("| %d | %s | %s | %.1f | %s | %s | %s | %s |" % (
            r["n"], r["lane"], r["type"], r["L"], r["ju"],
            "%.1f" % r["jL"] if r["jL"] else "-", "%.2f" % r["jH"] if r["jH"] else "-", r["note"]))
    print()
    for lane in D["tour"]:
        if lane.get("obstacles"):
            print("%s écarts (ft, sens de course) : %s" % (lane["id"], ", ".join("%.0f" % g for g in gaps(lane))))


if __name__ == "__main__":
    src = os.path.join(HERE, "refs", "5.webp")
    if os.path.exists(src):
        draw(src, os.path.join(HERE, "refs", "plan_annote.jpg"))
    table()
