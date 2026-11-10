var gateSoundPositions = [
	[561, 0, 302],
	[557, 0, 302],
	[553, 0, 302],
	[549, 0, 302],
	[545, 0, 302],
	[541, 0, 302],
	[537, 0, 302],
	[533, 0, 302],
	[529, 0, 302],
	[525, 0, 302],
	[521, 0, 302],
	[514, 0, 302],
	[510, 0, 302],
	[506, 0, 302],
	[502, 0, 302],
	[498, 0, 302],
	[494, 0, 302],
	[490, 0, 302],
	[486, 0, 302],
	[482, 0, 302],
	[478, 0, 302],
	[474, 0, 302]
];

var gateSounds = [];

var gateDropped = false;


for (var i=0; i < gateSoundPositions.length; i++) {
	gateSounds.push(mx.add_sound("@ZION.2025.SupercrossParis/sounds/gatedrop.sw"));
	mx.set_sound_freq(gateSounds[i], 32000);
	mx.set_sound_vol(gateSounds[i], 0.045);
	mx.set_sound_pos(gateSounds[i], gateSoundPositions[i][0], gateSoundPositions[i][1], gateSoundPositions[i][2]);
}

function gateSound(seconds) {
	var gateDropTime = mx.get_gate_drop_time();
	if (gateDropTime > 0.75 && !gateDropped ) {
		for (var i=0; i < gateSounds.length; i++) {
			mx.start_sound(gateSounds[i]);
		}
		gateDropped = true;
	}
}

mx.frame_handler = gateSound;

// Ambient crowd sounds
var g_ambient = mx.add_sound("@ZION.2025.SupercrossParis/sounds/crowd.wav");
var p = [], r = [];
mx.set_sound_freq(g_ambient, 44100);
mx.set_sound_vol(g_ambient, 0.4);
mx.set_sound_loop(g_ambient, 1);
mx.start_sound(g_ambient);

function updateCamPosition(seconds) {
   mx.get_camera_location(p, r);
   mx.set_sound_pos(g_ambient, p[0], p[1], p[2]);
   updateCamPrev(seconds);
}

var updateCamPrev = mx.frame_handler;
mx.frame_handler = updateCamPosition;

var g_avatars = [
	{ page: 1, row: 0, col: 1, re: /\bmiss.*\bpiggy\b/i },
	{ page: 1, row: 1, col: 0, re: /\bgonzo\b/i },
	{ page: 1, row: 1, col: 1, re: /\bfozzy.*\bbear\b/i },
	{ page: 1, row: 2, col: 0, re: /\browlf\b/i },
	{ page: 1, row: 2, col: 1, re: /\bscooter\b/i },
	{ page: 1, row: 3, col: 0, re: /\bpepe.*\bprawn\b/i },
	{ page: 1, row: 3, col: 1, re: /\brizzo.*\brat\b/i },
	{ page: 1, row: 4, col: 0, re: /\bbunsen.*\bhoneydew\b/i },
	{ page: 1, row: 4, col: 1, re: /\bbeaker\b/i },
	{ page: 1, row: 5, col: 0, re: /\bwaldorf\b/i },
	{ page: 1, row: 5, col: 1, re: /\bstatler\b/i },

	/* catch all - this should be last */
	{ page: 1, row: 0, col: 0, re: /.*/ },
];

var g_scoretower_tid = mx.read_texture("@ZION.2025.SupercrossParis/statue/scoretower.seq");

function break_time(t) {
	var min, sec, ms;

	ms = Math.floor(t * 1000.0);
	sec = Math.floor(ms / 1000);
	min = Math.floor(sec / 60);

	ms -= sec * 1000;
	sec -= min * 60;

	return { min: min, sec: sec, ms: ms };
}

function left_fill_string(s, pad, n) {

	n -= s.length;

	while (n > 0) {
		if (n & 1)
			s = pad + s;

		n >>= 1;
		pad += pad;
	}

	return s;
}

function time_to_string(t) {
    var s;

    t = break_time(t);

    s = left_fill_string(t.min.toString(), " ", 0) + ":";
    s += left_fill_string(t.sec.toString(), "0", 2);

    return s;
}

function make_cell_map(f, s, d) {
	var i, m;

	m = [];

	d = s.indexOf(d);

	for (i = 0; i < 128; i++)
		m[String.fromCharCode(i)] = d;

	for (i = 0; i < s.length; i++)
		m[s[i]] = i;

	f.map = m;
}

var g_scoreboard_font = {
tid: g_scoretower_tid,
xoffset: 0,
yoffset: 0,
xscale: 1,
yscale: .25,
width: 1024,
height: 256,
line_height: 64,
overlap: 8,
coords: [ [ 0, 0, 24 ], [ 24, 0, 32 ], [ 56, 0, 48 ], [ 104, 0, 40 ],
[ 144, 0, 56 ], [ 200, 0, 48 ], [ 248, 0, 16 ], [ 264, 0, 32 ],
[ 296, 0, 32 ], [ 328, 0, 32 ], [ 360, 0, 40 ], [ 400, 0, 24 ],
[ 424, 0, 32 ], [ 456, 0, 24 ], [ 480, 0, 32 ], [ 512, 0, 40 ],
[ 552, 0, 40 ], [ 592, 0, 48 ], [ 640, 0, 48 ], [ 688, 0, 48 ],
[ 736, 0, 40 ], [ 776, 0, 40 ], [ 816, 0, 40 ], [ 856, 0, 40 ],
[ 896, 0, 40 ], [ 936, 0, 24 ], [ 960, 0, 32 ], [ 0, 64, 40 ],
[ 40, 64, 40 ], [ 80, 64, 40 ], [ 120, 64, 32 ], [ 152, 64, 56 ],
[ 208, 64, 48 ], [ 256, 64, 48 ], [ 304, 64, 48 ], [ 352, 64, 48 ],
[ 400, 64, 48 ], [ 448, 64, 48 ], [ 496, 64, 48 ], [ 544, 64, 48 ],
[ 592, 64, 32 ], [ 624, 64, 40 ], [ 664, 64, 48 ], [ 712, 64, 40 ],
[ 752, 64, 56 ], [ 808, 64, 48 ], [ 856, 64, 48 ], [ 904, 64, 48 ],
[ 952, 64, 48 ], [ 0, 128, 48 ], [ 48, 128, 48 ], [ 96, 128, 48 ],
[ 144, 128, 48 ], [ 192, 128, 48 ], [ 240, 128, 64 ], [ 304, 128, 56 ],
[ 360, 128, 48 ], [ 408, 128, 48 ], [ 456, 128, 40 ], [ 496, 128, 24 ],
[ 520, 128, 40 ], [ 560, 128, 40 ], [ 600, 128, 40 ], [ 640, 128, 24 ],
[ 664, 128, 40 ], [ 704, 128, 48 ], [ 752, 128, 40 ], [ 792, 128, 48 ],
[ 840, 128, 40 ], [ 880, 128, 40 ], [ 920, 128, 48 ], [ 968, 128, 40 ],
[ 0, 192, 32 ], [ 32, 192, 32 ], [ 64, 192, 48 ], [ 112, 192, 32 ],
[ 144, 192, 56 ], [ 200, 192, 40 ], [ 240, 192, 40 ], [ 280, 192, 48 ],
[ 328, 192, 48 ], [ 376, 192, 40 ], [ 416, 192, 40 ], [ 456, 192, 32 ],
[ 488, 192, 40 ], [ 528, 192, 40 ], [ 568, 192, 56 ], [ 624, 192, 48 ],
[ 672, 192, 48 ], [ 720, 192, 40 ], [ 760, 192, 40 ], [ 800, 192, 16 ],
[ 816, 192, 40 ], [ 856, 192, 40 ] ]
};

make_cell_map(g_scoreboard_font, 
 "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~",
 "*");

var g_scoreboard_numbers_font = {
tid: g_scoretower_tid,
xoffset: 0,
yoffset: .25,
xscale: 1,
yscale: 1,
width: 512,
height: 512,
line_height: 64,
overlap: 8,
coords: [ [ 0, 0, 48 ], [ 48, 0, 40 ], [ 88, 0, 48 ], [ 136, 0, 48 ],
[ 184, 0, 48 ], [ 232, 0, 48 ], [ 280, 0, 48 ], [ 328, 0, 48 ],
[ 376, 0, 48 ], [ 424, 0, 48 ], [ 472, 0, 32 ], [ 0, 64, 24 ],
[ 24, 64, 48 ], [ 72, 64, 40 ], [ 112, 64, 40 ], [ 152, 64, 48 ],
[ 200, 64, 32 ], [ 232, 64, 32 ], [ 264, 64, 48 ], [ 312, 64, 48 ],
[ 360, 64, 40 ] ]
};

make_cell_map(g_scoreboard_numbers_font, "0123456789:.FLahilnps", ".");

function get_cell_coords(f, c) {
	if (!(c in f.map))
		mx.message("Not in map " + c);
	return f.coords[f.map[c]];
}

function draw_text(f, x, y, s) {
	var i, c, sx, sy, dx, dy, w, h;

	dx = x;
	dy = y;

	for (i = 0; i < s.length; i++) {
		if (s[i] == "\n") {
			dx = x;
			dy += f.line_height / f.height * f.yscale;
			continue;
		}
		if (s[i] == " ") {
			c = get_cell_coords(f, ","); /* comma about as wide as space */
			dx += c[2] / f.width * f.xscale;
			continue;
		}
		c = get_cell_coords(f, s[i]);
		sx = c[0] / f.width * f.xscale + f.xoffset;
		sy = c[1] / f.height * f.yscale + f.yoffset;
		w = c[2] / f.width * f.xscale;
		h = f.line_height / f.height * f.yscale;
		mx.paste_custom_frame(f.tid, 0, sx, sy, dx, dy, w, h);
		dx += w - f.overlap / f.width * f.xscale;
	}
}

function measure_text(f, s) {
	var i, c, dx;

	dx = 0;

	for (i = 0; i < s.length; i++) {
		if (s[i] == "\n") {
			dx = 0;
			continue;
		}
		if (s[i] == " ") {
			c = ",".charCodeAt(i) - "!".charCodeAt(0); /* comma about as wide as space */
			dx += f.coords[c][2] / f.width * f.xscale;
			continue;
		}
		c = s.charCodeAt(i) - "!".charCodeAt(0);
		if (!(c in f.coords))
			c = "*".charCodeAt(i) - "!".charCodeAt(0);
		dx += (f.coords[c][2] - f.overlap) / f.width * f.xscale;
	}

	return dx;
}

var g_last_scoretower_update = 0;

var g_finish_laps = mx.get_finish_laps();
var g_finish_time = mx.get_finish_time();
var g_running_order;

var g_brand_color_coords = {
	red: [ 128, 464 ],
	white: [ 192, 464 ],
	green: [ 128, 352 ],
	orange: [ 64, 464 ],
	yellow: [ 0, 464 ],
	blue: [ 64, 352 ],
	none: [ 0, 352 ]
};

var g_brand_regexps = [
	{ re: /^crf?[0-9]+/, color: "red" },
	{ re: /^fc[0-9]+/, color: "white" },
	{ re: /^kx[0-9]+/, color: "green" },
	{ re: /^[0-9]+sx/, color: "orange" },
	{ re: /^rmz?[0-9]+/, color: "yellow" },
	{ re: /^yz[0-9]+/, color: "blue" },
	{ re: /./, color: "none" },
];

function get_brand_color(model) {
	var i;

	for (i = 0; i < g_brand_regexps.length - 1; i++)
		if (model.match(g_brand_regexps[i].re))
			break;

	return g_brand_regexps[i].color;
}

var g_avatar_map = [];

function get_avatar(slot, name) {
	var i;

	if (slot in g_avatar_map)
		return g_avatar_map[slot];

	for (i = 0; i < g_avatars.length; i++)
		if (name.match(g_avatars[i].re)) {
			g_avatar_map[slot] = g_avatars[i];
			return g_avatar_map[slot];
		}

	return null;
}

function time_remaining() {
	var drop = mx.get_gate_drop_time();
	var secs = mx.seconds - drop;

	if (drop < 0 || secs < 0)
		return g_finish_time;

	return Math.max(0.0, g_finish_time - secs);
}

function index_reached_before(index, seconds) {
	var i, r, t;

	r = g_running_order;

	for (i = 0; i < r.length; i++) {
		t = mx.get_timing(r[i].slot, index);
		if (t >= 0 && t < seconds)
			return true;
	}

	return false;
}

function laps_before_time(seconds) {
	var r, i, last, t;

	if (seconds == 0)
		return 0;

	seconds += mx.get_gate_drop_time();

	r = g_running_order;

	last = mx.index_to_lap(r[0].position);

	/* search backwards to find leader's last lap before time expired */
	for (i = last; i > 0; i--) {
		t = mx.get_timing(r[0].slot, mx.lap_to_index(i));
		if (t < seconds)
			break;
	}

	/* search entire field forwards to find last lap before time expired */
	for (; i <= last; i++) {
		if (!index_reached_before(mx.lap_to_index(i), seconds))
			break;
	}

	return i - 1;
}

function laps_remaining() {
	var finish_lap;

	final_lap = laps_before_time(g_finish_time) + 1 + g_finish_laps;

	return final_lap - mx.index_to_lap(g_running_order[0].position);
}

function laps_remaining_string(l) {
	if (l == 0)
		return "Finish";
	if (l == 1)
		return "Final Lap";
	return l.toFixed(0) + " Laps"
}

function time_or_laps_remaining() {
	var t, l;

	if (g_finish_time == 0)
		return laps_remaining_string(g_finish_laps - mx.index_to_lap(g_running_order[0].position));

	t = time_remaining();

	if (t == 0) {
		l = laps_remaining();
		if (l <= g_finish_laps)
			return laps_remaining_string(l);
	}

	return time_to_string(t);
}

function do_update_score_tower(seconds) {
    var x, y, r, t, a, c;

    g_running_order = mx.get_running_order();
    r = g_running_order;
    a = [];

    // On garde 5 pilotes (comme ton script actuel)
    for (x = 0; x < 5 && x < r.length; x++) {
        if (r[x].position < 1)
            break;

        t = {};
        t.color = get_brand_color(mx.get_bike_model(r[x].slot));
        t.name = mx.get_rider_name(r[x].slot).replace(/\|.*/, "");
        t.number = mx.get_rider_number(r[x].slot);
        t.avatar = get_avatar(r[x].slot, t.name);

        if (t.avatar && ("color" in t.avatar))
            t.color = t.avatar.color;

        // Dernier mot du nom en MAJUSCULE
        t.shortName = t.name.trim().split(" ").pop().toUpperCase();

        a.push(t);
    }

    mx.begin_custom_frame(g_scoretower_tid);

    // Bandeau du haut
    for (x = 0; x < 4; x++) {
        mx.paste_custom_frame(
            g_scoretower_tid, 0,
            0.0 / 256.0, (352.0 - 56.0) / 512.0,
            x * 64.0 / 256.0, 0.0 / 512.0,
            64.0 / 256.0, 112.0 / 512.0
        );
    }

    // Temps restant (inchangé)
    draw_text(g_scoreboard_numbers_font,
        (64.0 / 256.0) - 0.03,
        ((56.0 - 32.0) / 512.0) + 0.08,
        time_or_laps_remaining()
    );

    // Overlay du bandeau haut
    for (x = 0; x < 4; x++) {
        mx.paste_custom_frame(
            g_scoretower_tid, 0,
            192.0 / 256.0, (352.0 - 56.0) / 512.0,
            x * 64.0 / 256.0, 0.0 / 512.0,
            64.0 / 256.0, 112.0 / 512.0
        );
    }

    // Lignes pilotes (statique)
    for (y = 0; y < 5; y++) {

        if (y < a.length)
            t = a[y];
        else
            t = { color: "none", shortName: "", number: "", avatar: null };

        c = g_brand_color_coords[t.color];

        // Fond de ligne
        for (x = 0; x < 4; x++) {
            mx.paste_custom_frame(g_scoretower_tid, 0,
                c[0] / 256.0, (c[1] - 40) / 512.0,
                x * 64.0 / 256.0, (112 + y * 80) / 512.0,
                64.0 / 256.0, 80.0 / 512.0
            );
        }

        // Avatar fixe
        if (t.avatar) {
            mx.paste_custom_frame(
                g_scoretower_tid,
                t.avatar.page,
                t.avatar.col / 2.0,
                t.avatar.row * 80.0 / 512.0,
                0.52,
                (112 + y * 80) / 512.0,
                128.0 / 256.0,
                80.0 / 512.0
            );
        }

        // Numéro de course (fixe)
        draw_text(
            g_scoreboard_font,
            0.25,
            (143.8 + 8 + y * 80) / 512.0,
            t.number.toString()
        );

        // NOM en MAJUSCULE
        draw_text(
            g_scoreboard_font,
            0.38,
            (112.0 + 40 + y * 80) / 512.0,
            t.shortName
        );
    }

    mx.end_custom_frame(g_scoretower_tid);
}


function update_score_tower(seconds) {
	try {
		do_update_score_tower(seconds);
	} catch (e) {
		mx.message("error: " + e.toString());
	}
	g_update_score_tower_prev(seconds);
}

var g_update_score_tower_prev = mx.frame_handler;
mx.frame_handler = update_score_tower;