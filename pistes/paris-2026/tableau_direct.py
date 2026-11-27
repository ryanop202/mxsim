"""v37 (Ryan : « sur la RF il y a une tour qui affiche les noms des pilotes qui défilent ; fais les nôtres, sur le grand écran du
milieu ») : classement EN DIRECT sur l'écran géant du fond (paddock26.screen), style Supercross Paris (coucher de soleil violet / rose).

Même principe que la tour de classement du pack RF (sx2026/models/scoretower), refait à notre façon (nos images, notre mise en page) :
  - une texture animée « direct.seq » (ANIM1, 1 seule image affichée) posée sur une dalle devant l'écran central ;
  - frills.js la redessine 16 fois par seconde avec mx.begin_custom_frame / paste_custom_frame / end_custom_frame :
      gauche : logo Supercross Paris + temps restant (ou « 3 TOURS », « DERNIER TOUR », « ARRIVEE ») ;
      droite : les 5 premiers, bande à la couleur de la marque de la moto, place fixe, « #numéro  NOM » qui défile
      (une ligne vers la droite, la suivante vers la gauche, comme la RF).
  - images : fond.png (image 0 : fond fixe) et lettres.png (image 1 : 2 polices + bandes), toutes deux 2048 x 512, le même rapport
    que la dalle (4 x 1) : paste_custom_frame prend la même taille (0-1) à la source et sur la dalle, donc tout est dessiné dans les
    images à sa taille d'affichage (comme la RF : bandes en tuiles répétées, une police par taille).
NON TESTÉ EN JEU : le format du .seq et les fonctions mx.* sont repris de la RF (qui marche), pas vérifiés ici ; le dessin est
vérifié avec un faux jeu (mêmes appels, images recomposées).

  tableau_direct.make(OUT, FOLDER, x, z, yaw)  -> ligne de statue à ajouter + écrit les fichiers et frills.js
"""
import os
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = "statue/paris/direct"
VW, VH = 2048, 512                     # dalle = écran virtuel 2048 x 512 (rapport 4 x 1), mêmes dimensions que fond.png et lettres.png
FONT = r"C:/Windows/Fonts/impact.ttf"
PETITE = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ#:.-'!?/&+()"          # noms, numéros, places
GRANDE = "0123456789:ADEINORSTUV"                                     # temps / « 3 TOURS » / « DERNIER TOUR » / « ARRIVEE »
ROW_Y0, ROW_H, ROW_DY = 66, 82, 89     # rangées du classement (px de la dalle)
GH_P, GH_G = ROW_H, 120                # hauteur des cases de la petite et de la grande police
LEFT_W = 520                           # panneau de gauche (logo + temps)
POS_X0, POS_X1 = 530, 620              # case de la place
NAME_X0 = 632                          # zone qui défile : NAME_X0 -> VW
TUILE = 128                            # largeur d'une tuile de bande
TIMER_Y = 330                          # haut de la grande police (temps restant)
# couleurs des bandes (marque de la moto) ; « none » = violet Supercross Paris
BANDES = dict(honda=(206, 18, 30), ktm=(245, 105, 0), kawasaki=(36, 160, 60), yamaha=(30, 64, 196), suzuki=(236, 200, 0),
              husqvarna=(225, 228, 236), gasgas=(200, 20, 40), triumph=(30, 30, 34), none=(108, 30, 140), place=(16, 6, 24))
# modèle de moto (mx.get_bike_model) -> marque (comme la tour RF : préfixes des modèles du jeu)
MARQUES = [(r"^crf?[0-9]+", "honda"), (r"^[0-9]+sx", "ktm"), (r"^kx[0-9]+", "kawasaki"), (r"^yz[0-9]+", "yamaha"),
           (r"^rmz?[0-9]+", "suzuki"), (r"^fc[0-9]+", "husqvarna"), (r"^mc[0-9]+", "gasgas"), (r"^tf[0-9]+", "triumph")]


def _font(px):
    return ImageFont.truetype(FONT, px)


def _police(im, chars, px, gh, y0):
    """lettres blanches à contour noir + petite ombre, rangées à partir de y0 ; renvoie {lettre: [x, y, w]} (px) et le bas."""
    f = _font(px); d = ImageDraw.Draw(im); x, y = 4, y0; cells = {}
    for ch in chars:
        l, t, r, b = d.textbbox((0, 0), ch, font=f, stroke_width=4); w = r - l + 10
        if x + w > VW - 4:
            x, y = 4, y + gh
        sh = Image.new("RGBA", (w, gh), (0, 0, 0, 0)); oy = (gh - (b - t)) // 2 - t
        ImageDraw.Draw(sh).text((5 - l + 3, oy + 3), ch, font=f, fill=(0, 0, 0, 160)); sh = sh.filter(ImageFilter.GaussianBlur(2))
        ImageDraw.Draw(sh).text((5 - l, oy), ch, font=f, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(10, 6, 16, 255))
        im.alpha_composite(sh, (x, y)); cells[ch] = [x, y, w]; x += w + 4
    return cells, y + gh


def _bande(col, w=TUILE, h=ROW_H):
    """tuile de bande d'une rangée : dégradé vertical + liseré rose en haut."""
    t = np.linspace(0, 1, h)[:, None, None]; c = np.array(col, float)
    a = np.broadcast_to(c * (1.18 - 0.45 * t), (h, w, 3)).copy(); a[:3] = (255, 80, 170)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def _lettres():
    """image 1 : petite police, grande police, puis une rangée de tuiles de bandes."""
    im = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
    P, y1 = _police(im, PETITE, 60, GH_P, 0)
    G, y2 = _police(im, GRANDE, 104, GH_G, y1)
    by = y2; assert by + ROW_H <= VH, "lettres.png pleine"
    for i, col in enumerate(BANDES.values()):
        im.alpha_composite(_bande(col), (i * TUILE, by))
    return im, P, G, by


def _fond(PD):
    """image 0 : fond fixe : coucher de soleil, panneau gauche avec logo, titre, emplacements vides des 5 rangées."""
    im = PD._sunset(VW, VH); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, LEFT_W, VH], fill=(26, 8, 40, 255))
    d.rectangle([LEFT_W - 4, 0, LEFT_W, VH], fill=(255, 80, 170, 255))
    PD.fitc(im, PD.lg("sxparis"), (20, 14, LEFT_W - 20, 270), 0.02)
    f = _font(44)
    d.text((LEFT_W + 16, 6), "CLASSEMENT EN DIRECT", font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(20, 6, 30))
    d.ellipse([LEFT_W + 520, 20, LEFT_W + 546, 46], fill=(255, 40, 60))
    d.text((LEFT_W + 556, 6), "LIVE", font=f, fill=(255, 255, 255), stroke_width=3, stroke_fill=(20, 6, 30))
    d.rectangle([40, 300, LEFT_W - 40, 302], fill=(255, 80, 170))
    for k in range(5):
        y = ROW_Y0 + k * ROW_DY
        d.rectangle([LEFT_W + 10, y, VW - 8, y + ROW_H], fill=(40, 12, 60, 255))
        d.rectangle([POS_X0, y, POS_X1, y + ROW_H], fill=(16, 6, 24, 255))
    return im


def _js(P, G, by, tex_path):
    """frills.js : le dessin du classement (px de la dalle, convertis en 0-1 au moment de coller)."""
    bandes = {k: i for i, k in enumerate(BANDES)}
    return r"""/*
USLAND Paris v37 - classement en direct sur l'ecran geant du fond (comme la tour de classement de la RF, refait pour Paris).
Texte ASCII expres. Non teste en jeu.
*/
var TD_TEX = mx.read_texture("%(tex)s");
var TD_VW = %(vw)d, TD_VH = %(vh)d;
var TD_P = { h: %(ghp)d, c: %(P)s };     /* petite police : lettre -> [x, y, largeur] (px de lettres.png) */
var TD_G = { h: %(ghg)d, c: %(G)s };     /* grande police */
var TD_BANDES = %(bandes)s, TD_BY = %(by)d, TD_TUILE = %(tuile)d, TD_RH = %(rh)d;
var TD_MARQUES = [%(marques)s];
var TD_FIN_TOURS = mx.get_finish_laps(), TD_FIN_TEMPS = mx.get_finish_time();
var td_last = 0, td_ordre = [];

/* copie un rectangle (px) de l'image f vers la dalle (meme taille : les images ont la taille de la dalle) */
function td_cp(f, sx, sy, dx, dy, w, h) {
    mx.paste_custom_frame(TD_TEX, f, sx / TD_VW, sy / TD_VH, dx / TD_VW, dy / TD_VH, w / TD_VW, h / TD_VH);
}
function td_texte(f, x, y, s) {      /* ecrit s en (x, y) avec la police f ; renvoie la largeur */
    var i, c, x0 = x;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { x += f.h * 0.3; continue; }
        c = f.c[s[i]] || f.c["-"] || f.c["0"];
        td_cp(1, c[0], c[1], x, y, c[2], f.h);
        x += c[2] - 8;
    }
    return x - x0;
}
function td_largeur(f, s) {
    var i, c, w = 0;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { w += f.h * 0.3; continue; }
        c = f.c[s[i]] || f.c["-"] || f.c["0"]; w += c[2] - 8;
    }
    return w;
}
function td_bande(b, x0, x1, y) {    /* tuiles de la bande b de x0 a x1 */
    var x, w;
    for (x = x0; x < x1; x += TD_TUILE) { w = Math.min(TD_TUILE, x1 - x); td_cp(1, b * TD_TUILE, TD_BY, x, y, w, TD_RH); }
}
function td_marque(m) {
    var i;
    for (i = 0; i < TD_MARQUES.length; i++) if (m.match(TD_MARQUES[i][0])) return TD_MARQUES[i][1];
    return "none";
}
function td_chiffres(n, l) { n = n.toString(); while (n.length < l) n = "0" + n; return n; }
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
function td_tours_avant(secs) {      /* dernier tour commence avant la fin du temps (meme calcul que la RF) */
    var i, last, t;
    if (secs == 0) return 0;
    secs += mx.get_gate_drop_time();
    last = mx.index_to_lap(td_ordre[0].position);
    for (i = last; i > 0; i--) { t = mx.get_timing(td_ordre[0].slot, mx.lap_to_index(i)); if (t < secs) break; }
    for (; i <= last; i++) if (!td_passe_avant(mx.lap_to_index(i), secs)) break;
    return i - 1;
}
function td_tours_txt(l) {
    if (l <= 0) return "ARRIVEE";
    if (l == 1) return "DERNIER TOUR";
    return l.toFixed(0) + " TOURS";
}
function td_haut() {
    var t, l;
    if (td_ordre.length == 0 || td_ordre[0].position < 1) {
        if (TD_FIN_TEMPS == 0) return td_tours_txt(TD_FIN_TOURS);
        t = TD_FIN_TEMPS;
    } else {
        if (TD_FIN_TEMPS == 0) return td_tours_txt(TD_FIN_TOURS - mx.index_to_lap(td_ordre[0].position));
        t = td_temps_restant();
        if (t == 0) {
            l = td_tours_avant(TD_FIN_TEMPS) + 1 + TD_FIN_TOURS - mx.index_to_lap(td_ordre[0].position);
            if (l <= TD_FIN_TOURS) return td_tours_txt(l);
        }
    }
    return Math.floor(t / 60).toString() + ":" + td_chiffres(Math.floor(t) %% 60, 2);
}
function td_dessine(secs) {
    var y, r, p, s, off, x0, w, yy, txt;
    if (secs - td_last < 1.0 / 16.0) return;
    td_last = secs;
    td_ordre = mx.get_running_order();
    mx.begin_custom_frame(TD_TEX);
    td_cp(0, 0, 0, 0, 0, TD_VW, TD_VH);                                   /* fond fixe */
    for (y = 0; y < 5; y++) {
        yy = %(ry0)d + y * %(rdy)d;
        if (y >= td_ordre.length || td_ordre[y].position < 1) continue;
        r = td_ordre[y];
        td_bande(TD_BANDES[td_marque(mx.get_bike_model(r.slot))], %(lx)d, TD_VW - 8, yy);
        /* "#numero  NOM" qui defile (une rangee sur deux dans l autre sens) */
        txt = "#" + mx.get_rider_number(r.slot) + "  " + mx.get_rider_name(r.slot).replace(/\|.*/, "").toUpperCase();
        w = TD_VW - %(nx)d;
        off = secs / 20.0 + y / 5.0; off -= Math.floor(off);
        if ((y & 1) == 0) off = 1.0 - off;
        x0 = %(nx)d + off * w;
        td_texte(TD_P, x0, yy, txt);
        td_texte(TD_P, x0 - w, yy, txt);
        /* ce qui a deborde a gauche : fond remis, puis la case de la place */
        td_cp(0, 0, yy, 0, yy, %(nx)d, TD_RH);
        td_bande(TD_BANDES["place"], %(px0)d, %(px1)d, yy);
        p = r.position.toString();
        td_texte(TD_P, (%(px0)d + %(px1)d) / 2 - td_largeur(TD_P, p) / 2, yy, p);
    }
    /* temps ou tours restants (panneau de gauche) */
    s = td_haut();
    if (td_largeur(TD_G, s) <= %(lw)d - 40) td_texte(TD_G, %(lw)d / 2 - td_largeur(TD_G, s) / 2, %(ty)d, s);
    else {                           /* trop large (DERNIER TOUR) : petite police, un mot par ligne */
        txt = s.split(" ");
        for (y = 0; y < txt.length && y < 2; y++)
            td_texte(TD_P, %(lw)d / 2 - td_largeur(TD_P, txt[y]) / 2, %(ty)d - 14 + y * TD_RH, txt[y]);
    }
    mx.end_custom_frame(TD_TEX);
}
function td_image(secs) {
    try { td_dessine(secs); } catch (e) { mx.message("classement : " + e.toString()); }
    td_prev(secs);
}
var td_prev = mx.frame_handler;
if (!td_prev) td_prev = function (s) {};
mx.frame_handler = td_image;
""" % dict(tex=tex_path, vw=VW, vh=VH, ghp=GH_P, ghg=GH_G, P=json.dumps(P), G=json.dumps(G), bandes=json.dumps(bandes), by=by,
           tuile=TUILE, rh=ROW_H, marques=", ".join('[/%s/, "%s"]' % (r, k) for r, k in MARQUES), ry0=ROW_Y0, rdy=ROW_DY,
           lx=LEFT_W + 10, nx=NAME_X0, px0=POS_X0, px1=POS_X1, lw=LEFT_W, ty=TIMER_Y)


def make(OUT, FOLDER, x, z, yaw):
    """écrit fond.png, lettres.png, direct.seq, dalle.jm (statue/paris/direct) et frills.js ; renvoie la ligne de statue."""
    import paddock26 as PD
    D = os.path.join(OUT, *SUB.split("/")); os.makedirs(D, exist_ok=True)
    _fond(PD).convert("RGB").save(os.path.join(D, "fond.png"))
    let, P, G, by = _lettres()
    let.save(os.path.join(D, "lettres.png"))
    assert max(len(P), len(G)) and all(len(c) == 3 for c in list(P.values()) + list(G.values()))
    seq = ["ANIM1 1 2 2048 0", "0", "PNG @%s/%s/fond.png" % (FOLDER, SUB), "PNG @%s/%s/lettres.png" % (FOLDER, SUB), ""]
    open(os.path.join(D, "direct.seq"), "w", newline="\n").write("\n".join(seq))
    # dalle : devant l'écran central (paddock26.screen : panneau à z local 1,02), même largeur, hauteur au rapport 4 x 1
    m = PD.M(); w = PD.SCR_W; hgt = w / 4.0; y0 = (PD.SCR_Y0 + PD.SCR_Y1) / 2 - hgt / 2
    assert hgt <= PD.SCR_Y1 - PD.SCR_Y0
    m.panel((0, 1.10), (0, 1), w, hgt, y0, (0.0, 0.0, 1.0, 1.0))
    PD.write_jm(os.path.join(D, "dalle.jm"), [(PD.UNLIT, m)])
    tex = "@%s/%s/direct.seq" % (FOLDER, SUB)
    open(os.path.join(OUT, "frills.js"), "w", newline="\n", encoding="ascii").write(_js(P, G, by, tex))
    return ("[%.6f 0.000000 %.6f] %.6f @%s/%s/dalle.jm %s null" % (x, z, yaw, FOLDER, SUB, tex),
            dict(lettres=[len(P), len(G)], dalle_ft=[w, round(hgt, 1)]))
