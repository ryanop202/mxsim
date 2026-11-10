# 14 — Reprendre Paris 2026 sur un autre PC (pour un pote de Ryan)

## A. À faire à la main (avant de lancer Claude)

1. Ryan t'invite sur le dépôt privé `ryanop202/mxsim` (GitHub > Settings > Collaborators). Accepte l'invitation.
2. Installe : Git, Python 3.12 (coche « Add to PATH »), Node.js LTS, Claude Code.
3. Récupère le dépôt :
   ```bash
   git clone -b paris-2026 https://github.com/ryanop202/mxsim.git
   ```
4. Rien d'autre à récupérer : les photos (`paris2026/refs/photos2025/`) et l'archive ZION déjà extraite
   (`paris2026/refs/zion25_full/`) sont dans le dépôt.
5. Ouvre Claude Code dans le dossier `mxsim` et colle le prompt ci-dessous.

## B. Prompt à coller dans Claude Code

```text
Tu reprends le projet mxsim (piste MX Simulator « USLAND: Supercross Paris 2026 »), branche paris-2026.
Je ne suis pas Ryan, je suis un pote qui l'aide. Réponds en français, simple et structuré.

1. Lis d'abord : CLAUDE.md, paris2026/README.md (surtout « Habillage » à la fin), docs/12_objets_usland.md,
   puis paris2026/habillage.py, paris2026/hab_objets.py, paris2026/hab_kit.py, paris2026/layout_paris.py.

2. Installe et prépare (Windows, Python 3.12 : utilise « py -3.12 -I », pas 3.15 comme dans les vieilles docs) :
   - git pull
   - py -3.12 -m pip install -r requirements.txt
   - npm install
   - l'archive ZION est déjà extraite dans paris2026/refs/zion25_full/ZION.2025.SupercrossParis/ (versionnée)
   - les photos de référence sont dans paris2026/refs/photos2025/ (versionnées)

3. Construis dans cet ordre et vérifie que ça finit sur « contrôles : 7 / 7 » et « problems: [] » :
   py -3.12 -I stade_paris/src/build.py --mx
   py -3.12 -I paris2026/build_paris.py
   py -3.12 -I stade_paris/src/validate_mx.py tracks/USLAND2026SupercrossParis
   py -3.12 -I paris2026/profils.py
   py -3.12 -I paris2026/preview_track.py
   py -3.12 -I paris2026/apercu_habillage.py
   py -3.12 -I stade_paris/src/preview_web.py
   Aperçu 3D : py -3.12 -m http.server 8765 -d stade_paris/build/web puis http://localhost:8765

4. Où on en est (commit 7f0a35c, v5) : le TERRAIN est corrigé d'après les retours de Ryan (virages 90 moins hauts,
   sauts ZION lissés, réception du saut du milieu carrée, petit double avant l'arrivée, 2e bosse remise après la table
   des whoops, bosse du couloir Est sans ondulations, nouvel enchaînement tribune Sud, arène agrandie x1,45).
   L'HABILLAGE n'a pas encore été refait pour ce terrain. À faire (retours de Ryan) :
   a. Boudins des whoops : FLY Racing (rouge, logo blanc assets/logos/fly_racing_white.png) au lieu du « R ».
   b. Tuff blocks (demi-tonneaux) : posés SUR les bosses, au bord du dessus des sauts (pas entre les couloirs).
   c. Virages à berm : blocs durs gris un peu DANS le virage (bord du couloir), ballots / mur à sponsor EN HAUT du berm,
      filet juste derrière (voir photo 20.png : mur Honda sur le haut du berm, bâche grise dessous).
   d. Bâche AMV : pas sur l'appel mais sur les DEUX CÔTÉS de la réception du saut du milieu (réception maintenant
      carrée, côtés presque verticaux) ; la bâche suit la forme de la réception (panneau central + pentes).
   e. Arche 50 Factory : sur la PREMIÈRE bosse du couloir tribune Sud (L6), pas sur la dernière.
   f. Saut d'arrivée : la rampe acier + coins Honda doit commencer au pied de l'appel (là elle traînait au sol).
   g. Départ : enlever les boudins Motul le long du couloir de départ (« ça va pas du tout »).
   h. Long tuff block quand le tour reprend la ligne de départ après l'arrivée, pour diriger les pilotes. Il ne doit
      APPARAÎTRE QU'APRÈS LE DÉPART, environ 20 s après (sinon il gêne le départ). Regarde si MX Simulator permet ça
      (exemple : paris2026/refs/zion25_full/ZION.2025.SupercrossParis/frills.js, script de piste). Si c'est
      impossible, dis-le avant de faire autre chose et propose une solution.
   i. Paddock : camions perpendiculaires au mur de l'écran (nez vers le mur, arrière vers la piste), sur une rangée,
      avec la place gagnée par l'agrandissement (voir photo 1.webp).
   j. Vrais logos à télécharger (Ryan a dit oui) : AMV, Venum, Minerva Oil, Thor, Five, Moto Verte -> assets/logos/,
      puis les utiliser dans hab_kit.logo() à la place des versions redessinées en texte.

5. Règles : pose des questions si un point n'est pas clair. Montre les aperçus (vue de dessus
   paris2026/apercu/vue_dessus_habillage.png + captures de l'aperçu 3D) AVANT de dire que c'est fini.
   Ne dis jamais que la piste marche en jeu : « non testé en jeu ». Logos jamais déformés ni en miroir.
   Commits en français, courts, sur paris-2026 ; git pull avant de commencer et git push souvent
   (Ryan travaille aussi sur le dépôt). Ne mets pas le .rar lui-même sur GitHub (le dossier extrait y est déjà).
```
