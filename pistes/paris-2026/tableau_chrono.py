"""v45d - écran géant en tableau de chronométrage (DA « bureautique » d'après la photo de l'utilisateur : écran de chrono d'une
manche SX2), à la place du classement TV.

« Une colonne bleue avec la place ; un bandeau rouge avec les titres ; le numéro en blanc ; NOM Prénom ; (nationalité et drapeau :
enlevés) ; la marque ; le nombre de tours ; le temps total ; l'écart avec le premier ; son meilleur tour ; le temps au tour (le
dernier qu'il vient de faire). En haut, en vert le temps qu'ils ont fait et en rouge le temps qui reste (pas le titre, pas les
drapeaux, pas l'heure). En dessous : « Meill TR : temps (numéro) nom ». Aucun logo. Police fine, bureautique. »

L'écran (4 panneaux carrés de 256 px côte à côte, textures direct_a = panneaux 1-2, direct_b = panneaux 3-4, comme tableau_direct)
= un seul tableau de 1024 x 256 px : chaque colonne tient dans un panneau (le texte ne traverse jamais une limite de panneau).
Fond (statique) : fond_a / fond_b ; texte (à chaque image) : lettres.png (Arial, 4 couleurs). Mêmes calculs que le jeu (portes de
chrono : get_timing / index_to_lap / lap_to_index).
"""
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PW, PH = 256, 512
# couleurs et police du logiciel de chrono (capture Chronelec Elite de l'utilisateur : « pour les couleurs c'est ça à peu près, et
# regarde la police ») : fond noir, bandeau des titres bleu pur, titres blancs en Tahoma gras, temps écoulé vert, messages jaunes
FONT = r"C:/Windows/Fonts/tahoma.ttf"           # « assez fin, bureautique »
FONT_B = r"C:/Windows/Fonts/tahomabd.ttf"
FOND, LIGNE1, LIGNE2 = (0, 0, 0), (0, 0, 0), (12, 12, 14)
BLEU_TITRES, BLEU_PLACE, BOITE_NUM = (214, 40, 40), (0, 0, 200), (226, 226, 228)   # v45d (« la ligne des titres en rouge, pas en bleu ») : bandeau rouge
BLANC, NOIR, VERT, ROUGE, JAUNE = (255, 255, 255), (0, 0, 0), (0, 230, 0), (240, 40, 40), (255, 255, 0)
# v45e (« tu peux aller plus loin que le 10e ; même place que les 10 de la dernière fois, jusqu'en bas de l'écran, toute la largeur ») :
# 2 moitiés côte à côte (places 1-11 à gauche, 12-22 à droite : les 22 grilles), 11 lignes chacune, toutes les colonnes dans chaque moitié
# v45f (« non : seulement les 11 qui ont la place, sur toute la longueur, pas 2 colonnes ; espace un peu plus les sections, même le
# meilleur tour ») : un seul tableau de 11 lignes sur toute la largeur de l'écran, colonnes réparties sur les 4 panneaux
N_LIGNES, N_MOITIES, MOITIE = 11, 1, 1024
Y_TITRES, H_TITRES, Y0, H = 20, 16, 38, 17                     # px de l'écran entier (256 de haut)
Y_BAS = Y0 + N_LIGNES * H + 4                                  # ligne du meilleur tour
GH = 16                                                        # hauteur d'une cellule de lettre
TAILLE = 13
# colonnes (x 0-1023 ; ancre : g = gauche, d = droite, c = centre) ; chaque colonne dans un seul panneau de 256
COLS = dict(pos=(6, 34, "c"), num=(44, 88, "c"), nom=(100, 252, "g"),
            marque=(272, 382, "c"), tours=(412, 482, "c"),
            total=(536, 636, "d"), ecart=(666, 756, "d"),
            meill=(796, 884, "d"), tour=(924, 1012, "d"))
TITRES = dict(pos="Pos.", num="N°", nom="Pilote", marque="Marque", tours="Tours", total="Tps total", ecart="Ecart", meill="M. Tour", tour="Tps. tour")
X_MT_T, X_MT_N, X_MT_P = 90, 166, 272                          # bas : temps, (N° x), nom (panneau 2) : espacés
X_VERT, X_ROUGE = (780, 884), (900, 1012)                       # haut, panneau 4 : temps écoulé (vert), temps / tours restants (rouge)
X_MT_LABEL, X_MT = 8, 72                                        # bas, panneau 1 : « Meill TR : » puis temps (numéro) nom
CH_B = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:.-+()'éè°"
CH_N = "0123456789"
CH_V = "0123456789:.-"
CH_R = "0123456789:.-+ LTOURS"
MARQUES_JS = [(r"^crf?[0-9]+", "Honda"), (r"^[0-9]+sx", "KTM"), (r"^kx[0-9]+", "Kawasaki"), (r"^yz[0-9]+", "Yamaha"),
              (r"^rmz?[0-9]+", "Suzuki"), (r"^fc[0-9]+", "Husqvarna"), (r"^mc[0-9]+", "GasGas"), (r"^tf[0-9]+", "Triumph")]


def _panneau(x):
    """(texture, x dans la page, y du carré) d'un x de l'écran entier."""
    k = int(x // 256)
    return ("a", "a", "b", "b")[k], x - 256 * k, (0, 256, 0, 256)[k]


def fonds():
    """pages 0 de direct_a / direct_b : bandeau rouge des titres, lignes, colonne bleue, cases blanches des numéros, « Meill TR : »."""
    big = Image.new("RGBA", (1024, 256), FOND + (255,)); d = ImageDraw.Draw(big)
    d.rectangle([0, Y_TITRES, 1023, Y_TITRES + H_TITRES - 1], fill=BLEU_TITRES + (255,))
    ft = ImageFont.truetype(FONT_B, 11)
    for m in range(N_MOITIES):
        o = m * MOITIE
        for k, (x0, x1, a) in COLS.items():
            xa = o + ((x0 + x1) / 2 if a == "c" else (x0 if a == "g" else x1))
            d.text((xa, Y_TITRES + H_TITRES / 2), TITRES[k], font=ft, fill=BLANC + (255,), anchor={"c": "mm", "g": "lm", "d": "rm"}[a])
        for i in range(N_LIGNES):
            y = Y0 + i * H
            d.rectangle([o, y, o + MOITIE - 4, y + H - 2], fill=(LIGNE1 if i % 2 == 0 else LIGNE2) + (255,))
            d.rectangle([o + COLS["pos"][0], y, o + COLS["pos"][1], y + H - 2], fill=BLEU_PLACE + (255,))
            d.rectangle([o + COLS["num"][0], y + 1, o + COLS["num"][1], y + H - 3], fill=BOITE_NUM + (255,))
    d.text((X_MT_LABEL, Y_BAS + GH / 2), "Meill TR :", font=ImageFont.truetype(FONT, TAILLE), fill=JAUNE + (255,), anchor="lm")
    A = Image.new("RGBA", (PW, PH)); B = Image.new("RGBA", (PW, PH))
    for k in range(4):
        tex, _, y0 = _panneau(256 * k)
        (A if tex == "a" else B).paste(big.crop((256 * k, 0, 256 * k + 256, 256)), (0, y0))
    return A, B


def _police(im, chars, path, px, col, y0):
    f = ImageFont.truetype(path, px); d = ImageDraw.Draw(im); x, y = 1, y0; cells = {}
    _, rt, _, rb = d.textbbox((0, 0), "H0", font=f)
    for ch in chars:
        l, t, r, b = d.textbbox((0, 0), ch, font=f); w = r - l + 2
        if x + w > PW - 1:
            x, y = 1, y + GH
        oy = (GH - (rb - rt)) // 2 - rt
        d.text((x + 1 - l, y + oy), ch, font=f, fill=col + (255,))
        cells[ch] = [x, y, w]; x += w + 1
    return cells, y + GH


def lettres():
    """page 1 : 4 polices (blanc, noir des numéros, vert, rouge)."""
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    Bc, y = _police(im, CH_B, FONT, TAILLE, BLANC, 0)
    Nc, y = _police(im, CH_N, FONT_B, TAILLE, NOIR, y)
    Vc, y = _police(im, CH_V, FONT, TAILLE, VERT, y)
    Rc, y = _police(im, CH_R, FONT, TAILLE, ROUGE, y)
    assert y <= PH, "page 1 pleine"
    return im, dict(B=dict(h=GH, c=Bc), N=dict(h=GH, c=Nc), V=dict(h=GH, c=Vc), R=dict(h=GH, c=Rc))


def js(polices, tex_a, tex_b):
    """script (ASCII) : dessine le tableau à chaque image ; les écarts / meilleurs tours recalculés 1 fois par seconde."""
    cols = {k: [v[0], v[1], v[2]] for k, v in COLS.items()}
    s = JS
    for k, v in dict(TA=tex_a, TB=tex_b, POLICES=json.dumps(polices), COLS=json.dumps(cols), NL=str(N_LIGNES), NM=str(N_MOITIES), MO=str(MOITIE), Y0=str(Y0), HL=str(H),
                     DY=str((H - 1 - GH) // 2), YBAS=str(Y_BAS), XMT=str(X_MT), XV=json.dumps(X_VERT), XR=json.dumps(X_ROUGE), MT=json.dumps([X_MT_T, X_MT_N, X_MT_P]),
                     YHAUT=str((Y_TITRES - GH) // 2), MARQUES=", ".join('[/%s/, "%s"]' % (r, m) for r, m in MARQUES_JS)).items():
        s = s.replace("@@" + k + "@@", v)
    s.encode("ascii")
    return s


JS = r"""/*
USLAND Paris v45d - ecran geant en tableau de chronometrage (Pos, N, Nom, Marque, Nb, Tps total, Ec 1er, Meill Tr, Tps tour),
temps ecoule en vert et temps restant en rouge en haut, meilleur tour en bas. Texte ASCII expres.
*/
var TC_TEX = [mx.read_texture("@@TA@@"), mx.read_texture("@@TB@@")];
var TC_F = @@POLICES@@;
var TC_COLS = @@COLS@@;
var TC_NL = @@NL@@, TC_NM = @@NM@@, TC_MO = @@MO@@, TC_Y0 = @@Y0@@, TC_H = @@HL@@, TC_DY = @@DY@@, TC_YBAS = @@YBAS@@, TC_XMT = @@XMT@@, TC_YHAUT = @@YHAUT@@;
var TC_XV = @@XV@@, TC_XR = @@XR@@, TC_MT = @@MT@@;
var TC_MARQUES = [@@MARQUES@@];
var TC_FIN_TOURS = mx.get_finish_laps(), TC_FIN_TEMPS = mx.get_finish_time();
var tc_ordre = [], tc_cur = -1, tc_stats = {}, tc_s = -100, tc_mt = [-1, -1];

function tc_larg(f, s) {
    var i, c, w = 0;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { w += 4; continue; }
        c = f.c[s[i]]; if (c) w += c[2] - 2;
    }
    return w;
}
function tc_txt(f, x, y, s) {                         /* x, y de l'ecran entier (1024 x 256) ; reste dans le panneau de x */
    var i, c, k = Math.floor(x / 256), t = (k < 2) ? 0 : 1, xp = x - 256 * k, yp = y + ((k % 2) ? 256 : 0);
    if (t != tc_cur) return;
    for (i = 0; i < s.length; i++) {
        if (s[i] == " ") { xp += 4; continue; }
        c = f.c[s[i]]; if (!c) continue;
        mx.paste_custom_frame(TC_TEX[t], 1, c[0] / 256, c[1] / 512, xp / 256, yp / 512, c[2] / 256, f.h / 512);
        xp += c[2] - 2;
    }
}
function tc_col(f, k, y, s, o) {                      /* texte dans la colonne k de la moitie qui commence en o, coupe a sa largeur */
    var c = TC_COLS[k], w = c[1] - c[0];
    while (s.length > 1 && tc_larg(f, s) > w) s = s.substring(0, s.length - 1);
    if (c[2] == "g") tc_txt(f, o + c[0], y, s);
    else if (c[2] == "d") tc_txt(f, o + c[1] - tc_larg(f, s), y, s);
    else tc_txt(f, o + (c[0] + c[1]) / 2 - tc_larg(f, s) / 2, y, s);
}
function td_nom(s) {                                 /* pour le module d'evenements (ev_nom) : dernier mot du nom, 9 lettres */
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(" ");
    return m[m.length - 1].toUpperCase().substring(0, 9);
}
function tc_2(n) { n = Math.floor(n).toString(); return n.length < 2 ? "0" + n : n; }
function tc_chrono(t) {                               /* 45.025 / 1:05.123 / 5:55.185 */
    var m = Math.floor(t / 60), s = t - 60 * m;
    if (m < 1) return s.toFixed(3);
    return m + ":" + (s < 10 ? "0" : "") + s.toFixed(3);
}
function tc_marque(m) {
    var i;
    for (i = 0; i < TC_MARQUES.length; i++) if (m.match(TC_MARQUES[i][0])) return TC_MARQUES[i][1];
    return "";
}
function tc_nom(s) {                                  /* "Sacha Coenen" -> "COENEN Sacha" */
    var m = s.replace(/\|.*/, "").replace(/^\s+|\s+$/g, "").split(/\s+/), n;
    if (m.length < 2) return m[0].toUpperCase();
    n = m.pop().toUpperCase();
    return n + " " + m.join(" ");
}
function tc_maj() {                                   /* tours, temps total, meilleur tour, dernier tour : 1 fois par seconde */
    var i, k, r, n, t1, t2, st, d = mx.get_gate_drop_time();
    if (mx.seconds >= tc_s && mx.seconds - tc_s < 1.0) return;
    tc_s = mx.seconds; tc_stats = {}; tc_mt = [-1, -1];
    for (i = 0; i < tc_ordre.length; i++) {
        r = tc_ordre[i]; n = mx.index_to_lap(r.position); st = { tours: n, total: -1, meill: -1, der: -1 };
        if (n >= 1 && d >= 0) { t2 = mx.get_timing(r.slot, mx.lap_to_index(n)); if (t2 >= 0) st.total = t2 - d; }
        for (k = 1; k < n; k++) {
            t1 = mx.get_timing(r.slot, mx.lap_to_index(k)); t2 = mx.get_timing(r.slot, mx.lap_to_index(k + 1));
            if (t1 >= 0 && t2 > t1) {
                st.der = t2 - t1;
                if (st.meill < 0 || t2 - t1 < st.meill) st.meill = t2 - t1;
            }
        }
        if (st.meill > 0 && (tc_mt[0] < 0 || st.meill < tc_mt[0])) tc_mt = [st.meill, r.slot];
        tc_stats[r.slot] = st;
    }
}
function tc_ecart(r, l) {                             /* ecart au premier au meme point de chrono, ou tours de retard */
    var L = mx.lap_to_index(2) - mx.lap_to_index(1), n, t0, t1;
    if (L > 0) { n = Math.floor((l.position - r.position) / L); if (n >= 1) return "+" + n + " L"; }
    t0 = mx.get_timing(l.slot, r.position); t1 = mx.get_timing(r.slot, r.position);
    if (t0 < 0 || t1 < 0) return "";
    return tc_chrono(Math.max(0, t1 - t0));
}
function tc_haut() {                                  /* [ecoule (vert), restant (rouge)] */
    var d = mx.get_gate_drop_time(), e = (d < 0 || mx.seconds < d) ? 0 : mx.seconds - d, r, l;
    var ec = tc_2(e / 3600) + ":" + tc_2((e % 3600) / 60) + ":" + tc_2(e % 60);
    if (TC_FIN_TEMPS > 0) {
        r = Math.max(0, TC_FIN_TEMPS - e);
        return [ec, tc_2(r / 60) + ":" + tc_2(r % 60) + (TC_FIN_TOURS > 0 ? " +" + TC_FIN_TOURS.toFixed(0) + " L" : "")];
    }
    l = TC_FIN_TOURS - (tc_ordre.length > 0 && tc_ordre[0].position >= 1 ? mx.index_to_lap(tc_ordre[0].position) : 0);
    return [ec, Math.max(0, l).toFixed(0) + " TOURS"];
}
function tc_page(t) {
    var i, r, st, y, s, h, f, mq, o;
    tc_cur = t;
    mx.begin_custom_frame(TC_TEX[t]);
    mx.paste_custom_frame(TC_TEX[t], 0, 0, 0, 0, 0, 1, 1);
    h = tc_haut();
    tc_txt(TC_F.V, TC_XV[1] - tc_larg(TC_F.V, h[0]), TC_YHAUT, h[0]);
    tc_txt(TC_F.R, TC_XR[1] - tc_larg(TC_F.R, h[1]), TC_YHAUT, h[1]);
    for (i = 0; i < TC_NL * TC_NM && i < tc_ordre.length; i++) {      /* v45e : places 1-11 a gauche, 12-22 a droite */
        r = tc_ordre[i];
        if (r.position < 1) break;
        st = tc_stats[r.slot] || { tours: 0, total: -1, meill: -1, der: -1 };
        y = TC_Y0 + (i % TC_NL) * TC_H + TC_DY; o = Math.floor(i / TC_NL) * TC_MO;
        tc_col(TC_F.B, "pos", y, (i + 1).toString(), o);
        tc_col(TC_F.N, "num", y, mx.get_rider_number(r.slot).toString(), o);
        tc_col(TC_F.B, "nom", y, tc_nom(mx.get_rider_name(r.slot)), o);
        mq = tc_marque(mx.get_bike_model(r.slot)); if (mq) tc_col(TC_F.B, "marque", y, mq, o);
        tc_col(TC_F.B, "tours", y, st.tours.toString(), o);
        if (st.total > 0) tc_col(TC_F.B, "total", y, tc_chrono(st.total), o);
        tc_col(TC_F.B, "ecart", y, i == 0 ? "-" : tc_ecart(r, tc_ordre[0]), o);
        f = (st.der > 0 && st.der == st.meill) ? TC_F.V : TC_F.B;           /* record perso au dernier tour : en vert */
        if (st.meill > 0) tc_col(f, "meill", y, tc_chrono(st.meill), o);
        if (st.der > 0) tc_col(f, "tour", y, tc_chrono(st.der), o);
    }
    if (tc_mt[0] > 0) {
        tc_txt(TC_F.B, TC_MT[0], TC_YBAS, tc_chrono(tc_mt[0]));                                   /* v45f : 3 parties espacees */
        tc_txt(TC_F.B, TC_MT[1], TC_YBAS, "(N\u00b0 " + mx.get_rider_number(tc_mt[1]) + ")");
        s = tc_nom(mx.get_rider_name(tc_mt[1]));
        while (s.length > 1 && TC_MT[2] - 256 + tc_larg(TC_F.B, s) > 250) s = s.substring(0, s.length - 1);
        tc_txt(TC_F.B, TC_MT[2], TC_YBAS, s);
    }
    mx.end_custom_frame(TC_TEX[t]);
}
function tc_image(secs) {
    try { ev_maj(); } catch (e) { mx.message("evenements : " + e.toString()); }
    try { tc_ordre = mx.get_running_order(); tc_maj(); tc_page(0); tc_page(1); } catch (e) { mx.message("classement : " + e.toString()); }
    tc_prev(secs);
}
var tc_prev = mx.frame_handler;
if (!tc_prev) tc_prev = function (s) {};
mx.frame_handler = tc_image;
"""


def apercu(fA, fB, let, polices, path_png):
    """aperçu de l'écran (mêmes positions que le script), avec un classement d'exemple."""
    frames = {"a": fA.copy(), "b": fB.copy()}
    P = polices

    def larg(f, s):
        return sum(4 if ch == " " else (f["c"][ch][2] - 2 if ch in f["c"] else 0) for ch in s)

    def txt(f, x, y, s):
        tex, xp, y0 = _panneau(x); xp = xp
        for ch in s:
            if ch == " ":
                xp += 4; continue
            if ch not in f["c"]:
                continue
            c = f["c"][ch]; frames[tex].alpha_composite(let.crop((c[0], c[1], c[0] + c[2], c[1] + f["h"])), (int(round(xp)), int(round(y0 + y)))); xp += c[2] - 2

    def col(f, k, y, s, o=0):
        x0, x1, a = COLS[k]
        while len(s) > 1 and larg(f, s) > x1 - x0:
            s = s[:-1]
        txt(f, o + (x0 if a == "g" else (x1 - larg(f, s) if a == "d" else (x0 + x1) / 2 - larg(f, s) / 2)), y, s)
    rows = [(84, "COENEN Sacha", "KTM", 8, "5:55.185", "-", "45.025", "45.985", 0), (60, "CLARK Seth", "Honda", 8, "6:00.680", "5.495", "46.016", "46.889", 0),
            (57, "TURNER Jesson", "Yamaha", 8, "6:02.516", "7.331", "45.992", "47.202", 0), (389, "PIETRE Jules", "Yamaha", 8, "6:03.307", "8.122", "46.243", "46.243", 1),
            (41, "HARRISSON Mitchell", "Kawasaki", 8, "6:04.506", "9.321", "46.250", "46.531", 0), (16, "THOMPSON Cole", "Yamaha", 8, "6:06.547", "11.362", "45.922", "45.922", 1),
            (20, "MILLER Henry", "Kawasaki", 8, "6:07.205", "12.020", "46.113", "46.113", 1), (402, "HICKS Michael", "KTM", 8, "6:11.773", "16.588", "46.597", "50.272", 0),
            (250, "LEDEAU Julien", "GasGas", 8, "6:15.030", "19.845", "46.552", "49.159", 0), (65, "LOPEZ Yannis", "Husqvarna", 7, "6:18.606", "+1 L", "47.741", "47.815", 0)]
    yh = (Y_TITRES - GH) // 2
    txt(P["V"], X_VERT[1] - larg(P["V"], "00:06:58"), yh, "00:06:58"); txt(P["R"], X_ROUGE[1] - larg(P["R"], "2 TOURS"), yh, "2 TOURS")
    import random
    rnd = random.Random(45); noms = ["ROBERT Alex", "DUPONT Hugo", "MARTIN Leo", "BERNARD Tom", "PETIT Noah", "DURAND Enzo", "LEROY Theo",
                                     "MOREAU Jules", "SIMON Lucas", "LAURENT Nathan", "LEFEBVRE Louis", "MICHEL Adam"]
    for k, nm in enumerate(noms):
        t = 6 * 60 + 20 + k * 2.3
        rows.append((rnd.randint(100, 999), nm, rnd.choice(["KTM", "Honda", "Yamaha", "Kawasaki", "GasGas", "Husqvarna", "Triumph"]), 7,
                     "%d:%06.3f" % (t // 60, t % 60), "+1 L", "%.3f" % (47.5 + rnd.random() * 2), "%.3f" % (48 + rnd.random() * 3), 0))
    for i, (num, nom, mq, nt, tot, ec, me, de, vert) in enumerate(rows[:N_LIGNES * N_MOITIES]):
        y = Y0 + (i % N_LIGNES) * H + (H - 1 - GH) // 2; o = (i // N_LIGNES) * MOITIE; f = P["V"] if vert else P["B"]
        col(P["B"], "pos", y, str(i + 1), o); col(P["N"], "num", y, str(num), o); col(P["B"], "nom", y, nom, o); col(P["B"], "marque", y, mq, o)
        col(P["B"], "tours", y, str(nt), o); col(P["B"], "total", y, tot, o); col(P["B"], "ecart", y, ec, o); col(f, "meill", y, me, o); col(f, "tour", y, de, o)
    txt(P["B"], X_MT_T, Y_BAS, "45.025"); txt(P["B"], X_MT_N, Y_BAS, "(N° 84)"); txt(P["B"], X_MT_P, Y_BAS, "COENEN Sacha")
    full = Image.new("RGBA", (1024, 256))
    for k in range(4):
        tex, _, y0 = _panneau(256 * k)
        full.paste(frames[tex].crop((0, y0, 256, y0 + 256)), (256 * k, 0))
    full = full.resize((2048, int(512 * 55.8 / 52.5)), Image.LANCZOS); full.save(path_png)
    return path_png
