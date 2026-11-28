"""Classement EN DIRECT sur TOUT l'écran géant du fond (paddock26.screen).

v39 (Ryan, capture de la retransmission « Supercross Paris 2026 - jour 1 » : « la même DA pour les résultats sur l'écran, en direct : le
temps en haut, les résultats ») ; v39b (capture en jeu de la v39 : la colonne s'affiche ; « les résultats doivent être sur tout le grand
écran, avec nos noms ; ça doit marcher quand on roule en course ») : l'écran (210 x 56 ft) = 4 panneaux carrés côte à côte :
  1. logo Supercross Paris, « CLASSEMENT LIVE », le temps restant dans la case gris foncé à filet blanc (« 04:32 + 1L ») ;
  2. 3. 4. les places 1-8, 9-16, 17-22 (22 grilles) : place dans une case blanche, filet à la couleur de la marque, numéro en rose
     (« 57. »), nom du pilote en blanc (dernier mot du nom, 9 lettres au plus) ; logo USLAND en bas du panneau 4.

Fait EXACTEMENT comme la tour de classement de ZION 2025 Supercross Paris, qui marche en jeu (et la v39 l'a montré : la colonne
s'affichait) : textures « ANIM1 1 2 512 0 » de 2 images 256 x 512 (page 0 : fonds ; page 1 : polices et filets), dessin
(mx.begin_custom_frame / paste_custom_frame / end_custom_frame) À CHAQUE IMAGE du jeu ; 2 textures (direct_a : panneaux 1-2,
direct_b : panneaux 3-4), chaque panneau = un carré 256 x 256 de l'image ; mêmes calculs de temps / tours restants que ZION.

  tableau_direct.make(OUT, FOLDER, x, z, yaw)  -> ligne de statue à ajouter + écrit les fichiers et frills.js
"""
import os
import re
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = "statue/paris/direct"
PW, PH = 256, 512                       # pages (comme ZION : 256 x 512) ; 2 panneaux carrés de 256 par image
NPAN = 8                                # rangées par panneau de classement
ROW_H = 32
POS_X0, POS_X1 = 4, 40                  # case blanche de la place
BAR_X0, BAR_X1 = 44, 50                 # filet de la marque
NUM_X = 55                              # numéro (rose)
NAME_X = 116                            # nom (blanc)
NAME_MAX = 9
FONT_B = r"C:/Windows/Fonts/ariblk.ttf"     # Arial Black (gras, comme l'habillage TV)
NOM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'."
NUM = "0123456789.-"                    # v43d : « - » après le numéro (était « . »)
POS = "0123456789"
TEMPS = "0123456789:+L"
VIOLET, VIOLET2, ROSE = (34, 10, 52), (52, 16, 78), (236, 48, 196)
BANDES = dict(honda=(214, 24, 36), ktm=(250, 110, 0), kawasaki=(60, 180, 60), yamaha=(30, 70, 210), suzuki=(245, 205, 0),
              husqvarna=(235, 238, 244), gasgas=(200, 20, 40), triumph=(120, 120, 128), none=(150, 60, 190))
MARQUES = [(r"^crf?[0-9]+", "honda"), (r"^[0-9]+sx", "ktm"), (r"^kx[0-9]+", "kawasaki"), (r"^yz[0-9]+", "yamaha"),
           (r"^rmz?[0-9]+", "suzuki"), (r"^fc[0-9]+", "husqvarna"), (r"^mc[0-9]+", "gasgas"), (r"^tf[0-9]+", "triumph")]
# panneaux : (texture, y du carré dans l'image, première place affichée ou None = panneau du temps)
PANNEAUX = [("a", 0, None), ("a", 256, 1), ("b", 0, 9), ("b", 256, 17)]
TIME_BOX = (16, 150, 240, 240)          # case du temps dans le panneau 1 (px du carré)
TIME_Y = 168


def _police(im, chars, path, px, gh, col, y0):
    """lettres rangées à partir de y0 (largeur de la page) ; renvoie {lettre: [x, y, largeur]} (px de la page) et le bas."""
    f = ImageFont.truetype(path, px); d = ImageDraw.Draw(im); x, y = 1, y0; cells = {}
    for ch in chars:
        l, t, r, b = d.textbbox((0, 0), ch, font=f); w = r - l + 2
        if x + w > PW - 1:
            x, y = 1, y + gh
        oy = (gh - (b - t)) // 2 - t
        d.text((x + 1 - l, y + oy), ch, font=f, fill=col + (255,))
        cells[ch] = [x, y, w]; x += w + 1
    return cells, y + gh


def _lettres():
    """page 1 (les 2 textures) : polices (nom blanc, numéro rose, place sombre, temps blanc) + filets de couleur."""
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    N, y = _police(im, NOM, FONT_B, 17, 26, (255, 255, 255), 0)
    P, y = _police(im, NUM, FONT_B, 17, 26, ROSE, y)
    D, y = _police(im, POS, FONT_B, 17, 26, (24, 10, 36), y)
    T, y = _police(im, TEMPS, FONT_B, 35, 56, (255, 255, 255), y)
    by = y; d = ImageDraw.Draw(im)
    for i, col in enumerate(BANDES.values()):
        d.rectangle([i * 10, by, i * 10 + 7, by + ROW_H - 1], fill=col + (255,))
    assert by + ROW_H <= PH, "page 1 pleine"
    return im, N, P, D, T, by


def _rangees(d, y0, n):
    for k in range(n):
        y = y0 + k * ROW_H
        d.rounded_rectangle([POS_X1 + 2, y + 2, PW - 4, y + ROW_H - 3], 4, fill=(48, 14, 72, 255))
        d.rounded_rectangle([POS_X0, y + 2, POS_X1, y + ROW_H - 3], 4, fill=(250, 250, 252, 255))


def _fonds(PD):
    """pages 0 des 2 textures."""
    import sys
    sys.path.insert(0, os.path.join(HERE, "stade_paris", "src"))
    from arena import branding as BR_
    u_ = BR_.logo_rgba(); us = Image.fromarray(np.dstack([np.clip(u_[..., :3], 0, 255), np.clip(u_[..., 3] * 255, 0, 255)]).astype(np.uint8), "RGBA")
    us = us.crop(us.getbbox())
    A = Image.new("RGBA", (PW, PH), VIOLET + (255,)); B = Image.new("RGBA", (PW, PH), VIOLET + (255,))
    # panneau 1 : coucher de soleil, logo, « CLASSEMENT LIVE », case du temps
    A.paste(PD._sunset(PW, 256), (0, 0)); dA = ImageDraw.Draw(A)
    PD.fitc(A, PD.lg("sxparis"), (12, 6, PW - 12, 104), 0.02)
    f = ImageFont.truetype(FONT_B, 15)
    dA.rectangle([0, 112, PW, 138], fill=VIOLET + (255,))
    dA.text((10, 114), "CLASSEMENT", font=f, fill=(255, 255, 255))
    dA.ellipse([PW - 66, 120, PW - 56, 130], fill=(255, 40, 60)); dA.text((PW - 52, 114), "LIVE", font=f, fill=(255, 255, 255))
    dA.rounded_rectangle(TIME_BOX, 8, fill=(28, 28, 34, 255))
    dA.rectangle([TIME_BOX[0] + 22, TIME_BOX[1] + 9, TIME_BOX[2] - 22, TIME_BOX[1] + 12], fill=(235, 235, 240, 255))
    _rangees(dA, 256, NPAN)
    dB = ImageDraw.Draw(B)
    _rangees(dB, 0, NPAN)
    _rangees(dB, 256, 6)
    # v39b (Ryan, capture : « sur le grand écran, remplace le USLAND entouré par le logo MX Sim Racing ») : logo de l'utilisateur, fond noir enlevé
    mx = Image.open(os.path.join(HERE, "..", "..", "commun", "assets", "logos", "user", "logo mxsim racing.png")).convert("RGBA"); b_ = np.asarray(mx).copy()
    b_[..., 3] = np.where(b_[..., :3].max(-1) > 38, 255, 0); mx = Image.fromarray(b_, "RGBA"); mx = mx.crop(mx.getbbox())
    PD.fitc(B, mx, (24, 256 + 6 * ROW_H + 10, PW - 24, PH - 8), 0.02)
    return A, B


def _js(N, P, D, T, by, tex_a, tex_b):
    bandes = {k: i for i, k in enumerate(BANDES)}
    return r"""/*
USLAND Paris by Ryan v39b - classement en direct sur tout l'ecran geant (DA de la retransmission Supercross Paris).
Fait comme la tour de classement de ZION 2025 Supercross Paris (pages 256 x 512, dessin a chaque image). Texte ASCII expres.
*/
var TD_A = mx.read_texture("%(ta)s");
var TD_B = mx.read_texture("%(tb)s");
var TD_W = %(pw)d, TD_H = %(ph)d;
var TD_N = { h: 26, c: %(N)s };
var TD_P = { h: 26, c: %(P)s };
var TD_D = { h: 26, c: %(D)s };
var TD_T = { h: 56, c: %(T)s };
var TD_BANDES = %(bandes)s, TD_BY = %(by)d;
var TD_MARQUES = [%(marques)s];
var TD_FIN_TOURS = mx.get_finish_laps(), TD_FIN_TEMPS = mx.get_finish_time();
var td_ordre = [];
var td_tex = TD_A;

function td_cp(f, sx, sy, dx, dy, w, h) {
    mx.paste_custom_frame(td_tex, f, sx / TD_W, sy / TD_H, dx / TD_W, dy / TD_H, w / TD_W, h / TD_H);
}
function td_larg(f, s) {
    var i, c, w = 0;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { w += 8; continue; }
        c = f.c[s[i]]; if (c) w += c[2] - 1;
    }
    return w;
}
function td_txt(f, x, y, s) {
    var i, c;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { x += 8; continue; }
        c = f.c[s[i]]; if (!c) continue;
        td_cp(1, c[0], c[1], x, y, c[2], f.h);
        x += c[2] - 1;
    }
}
function td_marque(m) {
    var i;
    for (i = 0; i < TD_MARQUES.length; i++) if (m.match(TD_MARQUES[i][0])) return TD_MARQUES[i][1];
    return "none";
}
function td_2(n) { n = Math.floor(n).toString(); return n.length < 2 ? "0" + n : n; }
function td_temps_restant() {
    var d = mx.get_gate_drop_time(), s = mx.seconds - d;
    if (d < 0 || s < 0) return TD_FIN_TEMPS;
    return Math.max(0.0, TD_FIN_TEMPS - s);
}
function td_passe_avant(index, secs) {
    var i, t;
    for (i = 0; i < td_ordre.length; i++) { t = mx.get_timing(td_ordre[i].slot, index); if (t >= 0 && t < secs) return true; }
    return false;
}
function td_tours_avant(secs) {
    var i, last, t;
    if (secs == 0) return 0;
    secs += mx.get_gate_drop_time();
    last = mx.index_to_lap(td_ordre[0].position);
    for (i = last; i > 0; i--) { t = mx.get_timing(td_ordre[0].slot, mx.lap_to_index(i)); if (t < secs) break; }
    for (; i <= last; i++) if (!td_passe_avant(mx.lap_to_index(i), secs)) break;
    return i - 1;
}
function td_haut() {
    var t, l, lead = td_ordre.length > 0 && td_ordre[0].position >= 1;
    if (TD_FIN_TEMPS == 0) {
        l = TD_FIN_TOURS - (lead ? mx.index_to_lap(td_ordre[0].position) : 0);
        return Math.max(0, l).toFixed(0) + "L";
    }
    t = td_temps_restant();
    if (t > 0 || !lead) return td_2(t / 60) + ":" + td_2(t %% 60) + (TD_FIN_TOURS > 0 ? " + " + TD_FIN_TOURS.toFixed(0) + "L" : "");
    l = td_tours_avant(TD_FIN_TEMPS) + 1 + TD_FIN_TOURS - mx.index_to_lap(td_ordre[0].position);
    return "00:00" + (l > 0 ? " + " + l.toFixed(0) + "L" : "");
}
function td_nom(s) {
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(" ");
    return m[m.length - 1].toUpperCase().substring(0, %(nmax)d);
}
function td_rangees(y0, k0, n) {                              /* places k0+1 .. k0+n dans le carre qui commence a y0 */
    var k, r, yy, p;
    for (k = k0; k < k0 + n && k < td_ordre.length; k++) {
        r = td_ordre[k];
        if (r.position < 1) break;
        yy = y0 + (k - k0) * %(rh)d + 3;
        p = td_2(k + 1);                                        /* v42 : la place (r.position = portes de chrono passees : 44) */
        td_txt(TD_D, (%(px0)d + %(px1)d) / 2 - td_larg(TD_D, p) / 2, yy, p);
        td_cp(1, TD_BANDES[td_marque(mx.get_bike_model(r.slot))] * 10, TD_BY, %(bx0)d, yy - 1, %(bw)d, %(rh)d - 4);
        td_txt(TD_P, %(nx)d, yy, mx.get_rider_number(r.slot).toString() + "-");
        td_txt(TD_N, %(nmx)d, yy, td_nom(mx.get_rider_name(r.slot)));
    }
}
function td_dessine(secs) {
    var s;
    td_ordre = mx.get_running_order();
    td_tex = TD_A;
    mx.begin_custom_frame(TD_A);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    s = td_haut();
    td_txt(TD_T, TD_W / 2 - td_larg(TD_T, s) / 2, %(ty)d, s);
    td_rangees(256, 0, %(npan)d);
    mx.end_custom_frame(TD_A);
    td_tex = TD_B;
    mx.begin_custom_frame(TD_B);
    td_cp(0, 0, 0, 0, 0, TD_W, TD_H);
    td_rangees(0, %(npan)d, %(npan)d);
    td_rangees(256, 2 * %(npan)d, 6);
    mx.end_custom_frame(TD_B);
}
function td_image(secs) {
    try { td_dessine(secs); } catch (e) { mx.message("classement : " + e.toString()); }
    td_prev(secs);
}
var td_prev = mx.frame_handler;
if (!td_prev) td_prev = function (s) {};
mx.frame_handler = td_image;
""" % dict(ta=tex_a, tb=tex_b, pw=PW, ph=PH, N=json.dumps(N), P=json.dumps(P), D=json.dumps(D), T=json.dumps(T), bandes=json.dumps(bandes),
           by=by, marques=", ".join('[/%s/, "%s"]' % (r, k) for r, k in MARQUES), nmax=NAME_MAX, rh=ROW_H, px0=POS_X0, px1=POS_X1,
           bx0=BAR_X0, bw=BAR_X1 - BAR_X0, nx=NUM_X, nmx=NAME_X, ty=TIME_Y, npan=NPAN)


def apercu(OUT, path_png, ordre=None, temps="04:32 + 1L"):
    """aperçu de l'écran entier (mêmes calculs que frills.js, rejoués en Python) : 4 panneaux côte à côte."""
    D_ = os.path.join(OUT, *SUB.split("/"))
    fA = Image.open(os.path.join(D_, "fond_a.png")).convert("RGBA"); fB = Image.open(os.path.join(D_, "fond_b.png")).convert("RGBA")
    f1 = Image.open(os.path.join(D_, "lettres.png")).convert("RGBA"); meta = json.load(open(os.path.join(D_, "polices.json")))
    frames = {"a": fA.copy(), "b": fB.copy()}

    def larg(f, s):
        return sum(8 if ch == " " else (f["c"][ch][2] - 1 if ch in f["c"] else 0) for ch in s)

    def txt(fr, f, x, y, s):
        for ch in s:
            if ch == " ":
                x += 8; continue
            if ch not in f["c"]:
                continue
            c = f["c"][ch]; fr.alpha_composite(f1.crop((c[0], c[1], c[0] + c[2], c[1] + f["h"])), (int(round(x)), int(round(y)))); x += c[2] - 1
    noms = ["TURNER", "THOMAS", "HARRIS", "CLARK", "PIETERS", "MILLER", "COEN", "HICKS", "MANZI", "SOULE", "POLLET", "LOPEZ",
            "VINCENT", "BRUN", "SIMON", "LEBEAU", "LAMARQUE", "BRIAND", "HUDSON", "EKER", "OPPLIGER", "BAZO"]
    mods = ["crf450", "yz450f", "kx450", "450sxf", "fc450", "rmz450", "mc450f", "crf250"]
    ordre = ordre or [(n_ * 7 % 900 + 2, nm, mods[i % len(mods)]) for i, (n_, nm) in enumerate(zip(range(1, 23), noms))]
    B = meta["bandes"]
    txt(frames["a"], meta["T"], PW / 2 - larg(meta["T"], temps) / 2, TIME_Y, temps)
    for k, (num, nom, mod) in enumerate(ordre):
        tex, y0 = ("a", 256) if k < NPAN else ("b", 0) if k < 2 * NPAN else ("b", 256)
        yy = y0 + (k % NPAN) * ROW_H + 3; p = "%02d" % (k + 1); fr = frames[tex]
        txt(fr, meta["D"], (POS_X0 + POS_X1) / 2 - larg(meta["D"], p) / 2, yy, p)
        mq = next((kk for r, kk in MARQUES if re.match(r, mod)), "none")
        fr.alpha_composite(f1.crop((B[mq] * 10, meta["by"], B[mq] * 10 + BAR_X1 - BAR_X0, meta["by"] + ROW_H - 4)), (BAR_X0, yy - 1))
        txt(fr, meta["P"], NUM_X, yy, "%d-" % num); txt(fr, meta["N"], NAME_X, yy, nom.upper()[:NAME_MAX])
    full = Image.new("RGBA", (4 * PW, 256))
    for i, (tex, y0, _) in enumerate(PANNEAUX):
        full.paste(frames[tex].crop((0, y0, PW, y0 + 256)), (i * PW, 0))
    full = full.resize((4 * PW * 2, int(256 * 2 * 55.8 / 52.5)), Image.LANCZOS)     # au rapport réel de l'écran
    full.save(path_png)
    return path_png


def make(OUT, FOLDER, x, z, yaw, apercu_png=None):
    """écrit fond_a/b.png, lettres.png, direct_a/b.seq, dalles.jm (statue/paris/direct) et frills.js ; renvoie la ligne de statue
    (une seule statue : le jm a 2 matières, une par texture)."""
    import paddock26 as PD
    import hab_kit as K
    D = os.path.join(OUT, *SUB.split("/")); os.makedirs(D, exist_ok=True)
    for old in os.listdir(D):                                           # v37 / v38c / v39 : anciens fichiers
        os.remove(os.path.join(D, old))
    A, B = _fonds(PD); A.save(os.path.join(D, "fond_a.png")); B.save(os.path.join(D, "fond_b.png"))
    let, N, P, Dg, T, by = _lettres()
    let.save(os.path.join(D, "lettres.png"))
    json.dump(dict(N=dict(h=26, c=N), P=dict(h=26, c=P), D=dict(h=26, c=Dg), T=dict(h=56, c=T), by=by,
                   bandes={k: i for i, k in enumerate(BANDES)}), open(os.path.join(D, "polices.json"), "w"))
    for t_ in ("a", "b"):
        seq = ["ANIM1 1 2 512 0", "0", "PNG @%s/%s/fond_%s.png" % (FOLDER, SUB, t_), "PNG @%s/%s/lettres.png" % (FOLDER, SUB), ""]
        open(os.path.join(D, "direct_%s.seq" % t_), "w", newline="\n").write("\n".join(seq))
    # 4 rectangles devant l'écran (paddock26.screen : plus d'image fixe, fond noir à 1 ft derrière), un statue par texture
    hs = PD.SCR_Y1 - PD.SCR_Y0; wp = PD.SCR_W / 4.0; lines = []
    for t_ in ("a", "b"):
        m = PD.M()
        for i, (tx, y0, _) in enumerate(PANNEAUX):
            if tx == t_:
                m.panel((-PD.SCR_W / 2 + wp * (i + 0.5), 1.05), (0, 1), wp, hs, PD.SCR_Y0, K.R((0, y0, PW, y0 + 256), PW, PH))
        PD.write_jm(os.path.join(D, "ecran_%s.jm" % t_), [(PD.UNLIT, m)])
        lines.append("[%.6f 0.000000 %.6f] %.6f @%s/%s/ecran_%s.jm @%s/%s/direct_%s.seq null" % (x, z, yaw, FOLDER, SUB, t_, FOLDER, SUB, t_))
    ta, tb = ("@%s/%s/direct_%s.seq" % (FOLDER, SUB, t_) for t_ in ("a", "b"))
    open(os.path.join(OUT, "frills.js"), "w", newline="\n", encoding="ascii").write(_js(N, P, Dg, T, by, ta, tb))
    ap = apercu(OUT, apercu_png or os.path.join(D, "..", "apercu_direct.png"))
    return lines, dict(lettres=[len(N), len(P), len(Dg), len(T)], panneaux=len(PANNEAUX), panneau_ft=[round(wp, 1), round(hs, 1)], apercu=ap)
