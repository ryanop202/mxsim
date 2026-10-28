"""Matériaux : texture MX Simulator + réglages JM + paramètres de prévisualisation Blender.

jm  : ligne matériau JM1 « exposant intensité r g b » (0 = pas de spéculaire)
env : facteur de réflexion d'environnement (bloc JM « -1 f r g b ») ; 0 = aucun
unlit : bloc « -2 » (pleine luminosité, pour écrans/LED/projecteurs)
"""

MATERIALS = {
    # béton architectural blanc de la couronne (panneaux à joints)
    "crown":         dict(tex="crown_panel.png", jm=(12, 1, .10, .10, .10), rough=.75),
    "concrete_white": dict(tex="concrete_white-repeat.png", jm=(12, 1, .08, .08, .08), rough=.8),
    "alu_white":     dict(tex="alu_white-repeat.png", jm=(40, 1, .35, .35, .35), rough=.35, metal=.3),
    "glass_scale":   dict(tex="glass_frit.png", jm=(90, 1, .6, .6, .6), rough=.08),
    "glass_dark":    dict(tex="glass_dark-repeat.png", jm=(120, 1, .8, .8, .8), rough=.04),
    "curtain_wall":  dict(tex="curtain_wall-repeat.png", jm=(120, 1, .7, .7, .7), env=.3, rough=.05),
    "roof":          dict(tex="roof_kalzip-repeat.png", jm=(30, 1, .3, .3, .3), rough=.45, metal=.5),
    "concrete_grey": dict(tex="concrete_grey-repeat.png", jm=(0, 0, 0, 0, 0), rough=.9),
    "seat":          dict(tex="seat_band-repeat.png", jm=(30, 1, .22, .22, .22), rough=.45),
    "steel_black":   dict(tex="steel_black-repeat.png", jm=(25, 1, .2, .2, .2), rough=.5, metal=.6),
    "steel_galv":    dict(tex="steel_galv-repeat.png", jm=(50, 1, .5, .5, .5), rough=.35, metal=.9),
    "wall_black":    dict(tex="wall_black-repeat.png", jm=(0, 0, 0, 0, 0), rough=.95),
    "screen_proj":   dict(tex="projection_screen.png", jm=(0, 0, 0, 0, 0), rough=.9),
    "screen_proj_on": dict(tex="projection_screen.png", unlit=True, rough=.9, emit=1.0),
    "led_off":       dict(tex="led_off-repeat.png", jm=(60, 1, .4, .4, .4), rough=.2),
    "led_ribbon":    dict(tex="led_ribbon-hrepeat.png", unlit=True, emit=1.0),
    "white_matte":   dict(tex="white_matte.png", jm=(0, 0, 0, 0, 0), rough=.9),
    "light":         dict(tex="light_emit.png", unlit=True, emit=6.0),
    "skin_light":    dict(tex="skin_light-repeat.png", jm=(80, 1, .45, .45, .45), rough=.15),
    "office":      dict(tex="office_ribbon-repeat.png", jm=(30, 1, .25, .25, .25), rough=.5),
    "roof_under":    dict(tex="roof_under-repeat.png", jm=(0, 0, 0, 0, 0), rough=.8),
    "grating":       dict(tex="grating-repeat.png", jm=(20, 1, .2, .2, .2), alpha=True, two_sided=True, metal=.6),
    # réglettes LED des écailles : aluminium le jour, émissives dans la variante nuit
    "led_strip":     dict(tex="alu_white-repeat.png", jm=(40, 1, .35, .35, .35), rough=.35, night_unlit=True),
    "railing":       dict(tex="railing-repeat.png", jm=(30, 1, .3, .3, .3), alpha=True, two_sided=True, metal=.6),
    "signage":       dict(tex="signage.png", jm=(20, 1, .2, .2, .2), alpha=True),
    "signage_int":   dict(tex="signage_interior.png", unlit=True, alpha=True, emit=1.0),
}
