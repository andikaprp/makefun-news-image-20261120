#!/usr/bin/env python3
"""One Day on Earth - Friday 20 November 2026.

Renders the day's news as a single 1024x1024 observatory page:
a midnight ink-blue sun-path map, a stat band, dispatch postcards,
a three-leg logbook of briefs, and a cutting-room box that holds
Thursday's news back on date discipline.

Reads data.json (same folder) so the page content is data-only to
change: add or edit stories there and re-run. Local rendering only;
the entrypoint main.py ships the finished entry.png.
"""

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W = H = 1024
MARGIN = 16
CW = W - 2 * MARGIN  # content width, 992

# --- palette: midnight observatory -------------------------------------
BG_TOP = (10, 22, 40)
BG_BOT = (6, 13, 25)
PANEL = (13, 27, 48)
PANEL_LINE = (38, 66, 102)
LAND = (22, 42, 68)
LAND_LINE = (52, 84, 120)
AMBER = (240, 178, 62)
AMBER_DEEP = (201, 138, 43)
CREAM = (243, 234, 216)
MUTED = (157, 180, 204)
FAINT = (110, 138, 170)
TEAL = (93, 179, 164)
SKY = (127, 163, 200)
CORAL = (217, 106, 74)
INK = (8, 17, 30)

FONT_DIR = Path("/usr/share/fonts/truetype")
SERIF_B = str(FONT_DIR / "dejavu" / "DejaVuSerif-Bold.ttf")
SERIF = str(FONT_DIR / "dejavu" / "DejaVuSerif.ttf")
SANS_B = str(FONT_DIR / "liberation" / "LiberationSans-Bold.ttf")
SANS = str(FONT_DIR / "liberation" / "LiberationSans-Regular.ttf")
SANS_I = str(FONT_DIR / "liberation" / "LiberationSans-Italic.ttf")

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def tw(draw, text, fnt):
    return draw.textlength(text, font=fnt)


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns list of lines that fit width."""
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if tw(draw, trial, fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def tracked(draw, xy, text, fnt, fill, tracking=2.0, anchor_right=False):
    """Draw letter-spaced caps text; returns total width used."""
    widths = [tw(draw, ch, fnt) for ch in text]
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x, y = xy
    if anchor_right:
        x -= total
    for ch, wch in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += wch + tracking
    return total


def tracked_width(draw, text, fnt, tracking=2.0):
    return sum(tw(draw, ch, fnt) for ch in text) + tracking * max(0, len(text) - 1)


# --- the world, simplified polygons in (lon, lat) -----------------------
EURASIA = [
    (-9, 37), (-9, 43), (-2, 44), (-1, 46), (-5, 48), (-1, 50), (3, 51),
    (7, 54), (8, 57), (10, 59), (5, 60), (5, 62), (10, 64), (14, 67),
    (18, 69), (25, 71), (32, 70), (40, 67), (50, 68), (60, 69), (70, 72),
    (80, 73), (90, 75), (100, 77), (110, 74), (120, 73), (130, 72),
    (140, 72), (150, 70), (160, 70), (170, 67), (178, 65), (170, 60),
    (162, 58), (156, 51), (150, 45), (142, 43), (140, 39), (138, 35),
    (133, 34), (129, 33), (126, 35), (122, 31), (120, 27), (118, 24),
    (114, 22), (110, 20), (108, 15), (109, 12), (107, 9), (104, 8),
    (103, 5), (101, 7), (99, 10), (98, 14), (95, 16), (92, 16),
    (91, 22), (89, 22), (86, 20), (83, 19), (80, 15), (79, 13), (77, 8),
    (75, 11), (73, 16), (72, 20), (69, 22), (66, 25), (61, 25),
    (57, 27), (59, 23), (55, 20), (52, 16), (48, 14), (43, 12),
    (42, 16), (39, 21), (35, 28), (34, 31), (36, 36), (33, 36),
    (30, 36), (27, 37), (24, 36), (22, 37), (19, 40), (16, 40),
    (13, 41), (12, 44), (10, 44), (7, 44), (3, 43), (0, 39), (-2, 37),
]
AFRICA = [
    (-6, 35), (-2, 35), (3, 37), (10, 37), (11, 34), (20, 32), (30, 31),
    (32, 31), (34, 28), (35, 24), (37, 22), (39, 21), (43, 12), (48, 11),
    (51, 12), (50, 10), (46, 5), (42, 0), (40, -6), (40, -12), (38, -18),
    (36, -22), (34, -26), (32, -29), (28, -33), (25, -34), (20, -35),
    (17, -32), (15, -27), (13, -18), (12, -12), (13, -6), (9, -1),
    (9, 4), (6, 4), (-2, 5), (-7, 4), (-12, 8), (-16, 12), (-17, 15),
    (-16, 20), (-15, 25), (-13, 28), (-9, 31),
]
MADAGASCAR = [(44, -12), (47, -14), (50, -16), (48, -20), (46, -24),
              (45, -25), (44, -20), (43, -16)]
NORTH_AMERICA = [
    (-168, 65), (-160, 58), (-150, 59), (-140, 70), (-130, 70),
    (-120, 71), (-110, 68), (-100, 68), (-95, 69), (-90, 69), (-85, 66),
    (-80, 64), (-78, 62), (-81, 58), (-84, 55), (-88, 52), (-92, 50),
    (-94, 48), (-90, 46), (-86, 46), (-82, 45), (-79, 43), (-75, 40),
    (-74, 38), (-76, 35), (-80, 32), (-81, 26), (-84, 24), (-87, 21),
    (-90, 20), (-94, 18), (-97, 16), (-101, 14), (-104, 17), (-106, 20),
    (-110, 23), (-114, 28), (-117, 33), (-122, 37), (-124, 42),
    (-124, 47), (-130, 54), (-140, 60), (-152, 58), (-162, 58),
]
GREENLAND = [(-45, 60), (-40, 63), (-32, 68), (-22, 70), (-20, 74),
             (-25, 78), (-35, 78), (-50, 76), (-55, 72), (-53, 66),
             (-50, 61)]
SOUTH_AMERICA = [
    (-79, 9), (-75, 10), (-72, 12), (-64, 11), (-60, 9), (-52, 5),
    (-50, 0), (-44, -3), (-38, -5), (-35, -8), (-39, -13), (-40, -20),
    (-42, -23), (-48, -26), (-52, -32), (-57, -35), (-58, -39),
    (-62, -41), (-65, -45), (-67, -50), (-69, -52), (-71, -54),
    (-73, -50), (-73, -44), (-73, -37), (-71, -30), (-70, -20),
    (-75, -15), (-77, -12), (-80, -6), (-81, -4), (-80, 1), (-77, 4),
    (-77, 7),
]
UK = [(-5, 50), (-3, 53), (-5, 55), (-3, 57), (-1, 58), (-2, 54),
      (-1, 52), (-3, 50)]
IRELAND = [(-10, 52), (-8, 51), (-6, 52), (-6, 54), (-8, 55), (-10, 54)]
JAPAN = [(130, 31), (131, 33), (133, 34), (135, 34), (137, 35),
         (139, 37), (140, 39), (141, 41), (142, 44), (144, 44),
         (142, 45), (140, 41), (139, 38), (136, 35), (133, 35),
         (131, 33)]
SUMATRA = [(95, 5), (100, 0), (104, -3), (106, -5), (103, -4), (99, 1),
           (96, 4)]
BORNEO = [(109, 1), (113, 3), (117, 5), (119, 2), (117, -2), (113, -3),
          (110, -2)]
JAVA = [(106, -6), (110, -7), (114, -8), (114, -9), (108, -8), (106, -7)]
NEW_GUINEA = [(131, -1), (136, -2), (141, -3), (146, -6), (150, -9),
              (147, -8), (142, -7), (137, -5), (132, -3)]
AUSTRALIA = [
    (114, -22), (113, -26), (115, -32), (118, -35), (124, -33),
    (129, -32), (132, -32), (135, -34), (137, -35), (139, -37),
    (141, -38), (145, -38), (147, -39), (150, -37), (153, -32),
    (153, -27), (151, -24), (146, -19), (143, -15), (142, -11),
    (142, -14), (141, -17), (140, -18), (136, -15), (135, -12),
    (132, -11), (130, -13), (126, -14), (122, -17), (118, -20),
]
NZ_NORTH = [(173, -35), (175, -37), (178, -38), (176, -40), (174, -41),
            (173, -39), (172, -37)]
NZ_SOUTH = [(167, -46), (169, -44), (171, -43), (173, -42), (172, -44),
            (170, -46), (168, -47)]
LANDMASSES = [EURASIA, AFRICA, MADAGASCAR, NORTH_AMERICA, GREENLAND,
              SOUTH_AMERICA, UK, IRELAND, JAPAN, SUMATRA, BORNEO, JAVA,
              NEW_GUINEA, AUSTRALIA, NZ_NORTH, NZ_SOUTH]
# small island dots: (lon, lat)
ISLAND_DOTS = [(121, 14), (121, 24), (80, 8), (115, -8), (100, 6),
               (-18, 65), (47, -19), (-155, 19), (167, -45), (138, 36)]


# --- dispatch art strips: small flat scenes, one per story --------------
ART_BG = (16, 34, 58)


def _sun(draw, cx, cy, r, fill=AMBER):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def _wave(draw, x, y, w, amp=3, step=14, fill=TEAL, width=2):
    pts = []
    for i in range(0, w + step, step):
        pts.append((x + i, y + (amp if (i // step) % 2 else -amp)))
    draw.line(pts, fill=fill, width=width)


def art_whale(d, x, y, w, h):
    d.rectangle([x, y + h - 9, x + w, y + h], fill=(13, 44, 62))
    _wave(d, x + 6, y + h - 12, w - 12)
    cx, cy = x + w * 0.42, y + h - 8
    d.polygon([(cx, cy), (cx - 16, cy - 15), (cx - 4, cy - 12),
               (cx, cy - 17), (cx + 4, cy - 12), (cx + 16, cy - 15)],
              fill=CREAM)
    d.rectangle([cx - 2, cy - 12, cx + 2, cy], fill=CREAM)
    for dx, dy in [(-26, -16), (-18, -21), (24, -18)]:
        d.ellipse([cx + dx - 1, cy + dy - 1, cx + dx + 1, cy + dy + 1],
                  fill=SKY)


def art_palm(d, x, y, w, h):
    _sun(d, x + w - 34, y + 10, 6)
    d.line([x, y + h - 4, x + w, y + h - 4], fill=AMBER_DEEP, width=2)
    for gx in range(x + 8, x + w - 8, 26):
        d.line([gx, y + h - 4, gx + 5, y + h - 9], fill=AMBER_DEEP, width=1)
    tx, ty = x + 44, y + h - 4
    d.line([tx, ty, tx + 6, y + 8], fill=CREAM, width=3)
    for ang in (-160, -120, -80, -40, -5):
        ex = tx + 6 + 15 * math.cos(math.radians(ang))
        ey = y + 8 + 9 * math.sin(math.radians(ang))
        d.line([tx + 6, y + 8, ex, ey], fill=TEAL, width=2)


def art_tower(d, x, y, w, h):
    cx = x + w * 0.4
    top = (cx + 7, y + 3)
    bl, br = (cx - 9, y + h - 2), (cx + 17, y + h - 2)
    d.line([top, bl], fill=CREAM, width=2)
    d.line([top, br], fill=CREAM, width=2)
    d.line([(cx - 4, y + h * 0.45), (cx + 13, y + h * 0.45)], fill=CREAM,
           width=1)
    d.line([(cx + 1, y + 9), (cx + 16, y + 9)], fill=CREAM, width=2)
    d.line([(cx - 3, y + 15), (cx + 19, y + 15)], fill=CREAM, width=2)
    bx, by = x + w * 0.68, y + 4
    d.polygon([(bx, by), (bx - 6, by + 11), (bx - 1, by + 11),
               (bx - 4, by + 20), (bx + 6, by + 8), (bx + 1, by + 8)],
              fill=AMBER)


def art_cyclone(d, x, y, w, h):
    cx, cy = x + w * 0.38, y + h * 0.48
    for r, a0 in [(13, 20), (9, 140), (5, 260)]:
        d.arc([cx - r, cy - r * 0.72, cx + r, cy + r * 0.72], a0, a0 + 250,
              fill=CREAM, width=2)
    _sun(d, cx, cy, 2, fill=AMBER)
    for i in range(6):
        rx = x + w * 0.58 + i * 11
        d.line([rx, y + 6, rx - 3, y + 12], fill=SKY, width=2)
        d.line([rx, y + 17, rx - 3, y + 23], fill=SKY, width=2)
    d.line([x + w * 0.55, y + h - 3, x + w - 6, y + h - 3], fill=TEAL,
           width=2)


def _chart(d, x, y, w, h, pts_frac, color):
    base = y + h - 5
    d.line([x + 6, base, x + w - 8, base], fill=FAINT, width=1)
    pts = [(x + 8 + fx * (w - 24), y + 4 + fy * (h - 12))
           for fx, fy in pts_frac]
    d.line(pts, fill=color, width=2)
    ex, ey = pts[-1]
    d.polygon([(ex, ey), (ex - 7, ey - 1), (ex - 2, ey + 5)], fill=color)
    return pts


def art_chart_down(d, x, y, w, h):
    _chart(d, x, y, w, h,
           [(0, 0.1), (0.2, 0.3), (0.4, 0.25), (0.6, 0.55), (0.8, 0.6),
            (1, 0.9)], CORAL)


def art_chart_up(d, x, y, w, h):
    _chart(d, x, y, w, h,
           [(0, 0.9), (0.2, 0.7), (0.4, 0.75), (0.6, 0.4), (0.8, 0.35),
            (1, 0.05)], TEAL)
    sx, sy = x + w - 26, y + 6
    for ang in range(0, 360, 45):
        d.line([sx, sy, sx + 5 * math.cos(math.radians(ang)),
                sy + 5 * math.sin(math.radians(ang))], fill=AMBER, width=1)


def art_shield(d, x, y, w, h):
    cx, cy = x + w * 0.55, y + h + 6
    d.arc([cx - 34, cy - 40, cx + 34, cy + 40], 180, 340, fill=TEAL, width=3)
    d.arc([cx - 25, cy - 31, cx + 25, cy + 31], 180, 340, fill=SKY, width=2)
    mx, my = x + w * 0.3, y + 5
    d.polygon([(mx, my), (mx + 16, my + 9), (mx + 12, my + 14),
               (mx - 2, my + 6)], fill=CREAM)
    d.polygon([(mx - 2, my + 6), (mx - 7, my + 12), (mx + 2, my + 12)],
              fill=CORAL)
    bx, by = x + w * 0.52, y + 8
    for ang in range(0, 360, 60):
        d.line([bx, by, bx + 6 * math.cos(math.radians(ang)),
                by + 6 * math.sin(math.radians(ang))], fill=AMBER, width=2)


def art_skyline(d, x, y, w, h):
    base = y + h
    bx = x + 8
    for bw, bh in [(16, 12), (11, 18), (19, 9), (13, 15), (17, 11),
                   (12, 17), (15, 10)]:
        d.rectangle([bx, base - bh, bx + bw, base], fill=(8, 18, 33))
        bx += bw + 5
    for t in range(3):
        sx = x + 30 + t * 52
        d.arc([sx, y + 1, sx + 44, y + 22], 300, 360, fill=AMBER, width=2)
    ex, ey = x + w - 34, y + 9
    for ang in range(0, 360, 45):
        d.line([ex, ey, ex + 5 * math.cos(math.radians(ang)),
                ey + 5 * math.sin(math.radians(ang))], fill=CORAL, width=2)


def art_globe(d, x, y, w, h):
    cx, cy, r = x + w * 0.4, y + h // 2, 12
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=TEAL, width=2)
    d.ellipse([cx - 5, cy - r, cx + 5, cy + r], outline=TEAL, width=1)
    d.line([cx - r, cy, cx + r, cy], fill=TEAL, width=1)
    lx, ly = x + w * 0.62, y + h - 9
    d.polygon([(lx, ly), (lx + 15, ly - 12), (lx + 17, ly - 3),
               (lx + 6, ly + 2)], fill=(110, 190, 110))
    d.line([lx + 1, ly - 1, lx + 16, ly - 11], fill=(16, 34, 58), width=1)


def art_flags(d, x, y, w, h):
    for i, (fx, col) in enumerate([(x + w * 0.36, TEAL),
                                   (x + w * 0.6, AMBER)]):
        d.line([fx, y + h - 2, fx, y + 4], fill=CREAM, width=2)
        d.polygon([(fx, y + 4), (fx + 17, y + 7 + i), (fx, y + 12)],
                  fill=col)
    for i in range(5):
        sx = x + w * 0.44 + (i % 3) * 7
        sy = y + 16 + (i // 3) * 7
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=SKY)


def art_pill(d, x, y, w, h):
    cx, cy = x + w * 0.42, y + h // 2
    d.rounded_rectangle([cx - 20, cy - 6, cx + 20, cy + 6], 6, fill=CREAM)
    d.rounded_rectangle([cx, cy - 6, cx + 20, cy + 6], 6, fill=CORAL)
    for dx, dy, r, col in [(52, -6, 4, TEAL), (66, 5, 3, SKY),
                          (84, -3, 5, TEAL), (98, 6, 3, AMBER)]:
        d.ellipse([cx + dx - r, cy + dy - r, cx + dx + r, cy + dy + r],
                  outline=col, width=2)


def art_vice(d, x, y, w, h):
    for r in (13, 9, 5):
        d.ellipse([x + w * 0.62 - r, y + 15 - r, x + w * 0.62 + r,
                   y + 15 + r], outline=AMBER_DEEP, width=1)
    _sun(d, x + w * 0.62, y + 15, 4)
    base = y + h
    bx = x + w * 0.72
    for bw, bh in [(12, 10), (9, 15), (13, 8)]:
        d.rectangle([bx, base - bh, bx + bw, base], fill=(8, 18, 33))
        bx += bw + 3
    for px in (x + 20, x + 44):
        d.line([px, base, px + 3, y + 10], fill=TEAL, width=2)
        for ang in (-150, -105, -60, -20):
            d.line([px + 3, y + 10,
                    px + 3 + 10 * math.cos(math.radians(ang)),
                    y + 10 + 7 * math.sin(math.radians(ang))],
                   fill=TEAL, width=2)
    d.rounded_rectangle([x + w * 0.3, base - 6, x + w * 0.44, base - 1], 2,
                        fill=CREAM)


ART_FUNCS = {
    "whale": art_whale, "palm": art_palm, "tower": art_tower,
    "cyclone": art_cyclone, "chart_down": art_chart_down,
    "chart_up": art_chart_up, "shield": art_shield,
    "skyline": art_skyline, "globe": art_globe, "flags": art_flags,
    "pill": art_pill, "vice": art_vice,
}


# --- layout --------------------------------------------------------------
def project(lon, lat, rect):
    x0, y0, x1, y1 = rect
    px = x0 + (lon + 180) / 360.0 * (x1 - x0)
    py = y0 + (74 - lat) / (74 + 58) * (y1 - y0)
    return px, py


def draw_map(d, data, rect):
    x0, y0, x1, y1 = rect
    for poly in LANDMASSES:
        pts = [project(lon, lat, rect) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_LINE)
    for lon, lat in ISLAND_DOTS:
        px, py = project(lon, lat, rect)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=LAND_LINE)
    # the sun's road: an amber arc over the top of the world
    import math as _m
    arc_pts = []
    for i in range(81):
        t = i / 80.0
        ax = x0 + 14 + t * (x1 - x0 - 28)
        ay = (y0 + 16) - _m.sin(t * _m.pi) * 13 + t * 4
        arc_pts.append((ax, ay))
    d.line(arc_pts, fill=AMBER_DEEP, width=2)
    sx, sy = arc_pts[40]
    _sun(d, sx, sy, 4)
    f_lab = font(SANS_B, 9)
    d.text((x0 + 8, y0 + 2), "DAWN", font=f_lab, fill=AMBER)
    mid_w = tw(d, "MIDDAY", f_lab)
    d.text(((x0 + x1) / 2 - mid_w / 2, y0 + 2), "MIDDAY", font=f_lab,
           fill=AMBER)
    dusk_w = tw(d, "DUSK", f_lab)
    d.text((x1 - 10 - dusk_w, y0 + 2), "DUSK", font=f_lab, fill=AMBER)
    # brief dots first, dispatch pins on top
    for s in data["stories"]:
        if s["kind"] != "brief":
            continue
        px, py = project(s.get("pin_lon", s["lon"]),
                         s.get("pin_lat", s["lat"]), rect)
        d.ellipse([px - 2.5, py - 2.5, px + 2.5, py + 2.5], fill=SKY)
    f_pin = font(SANS_B, 9)
    for s in data["stories"]:
        if s["kind"] != "dispatch":
            continue
        px, py = project(s.get("pin_lon", s["lon"]),
                         s.get("pin_lat", s["lat"]), rect)
        r = 8
        d.ellipse([px - r, py - r, px + r, py + r], fill=AMBER,
                  outline=INK, width=1)
        label = str(s["disp"])
        lw = tw(d, label, f_pin)
        d.text((px - lw / 2, py - 5.5), label, font=f_pin, fill=INK)


def card_height(d, s, inner_w):
    f_head = font(SERIF_B, 14.5)
    f_text = font(SANS, 9.5)
    hl = wrap(d, s["headline"], f_head, inner_w)
    tl = wrap(d, s["text"] + "  - " + s["source"], f_text, inner_w)
    return 47 + len(hl) * 18 + 3 + len(tl) * 11.5 + 7, hl, tl


def draw_card(d, s, x, y, w, h):
    d.rounded_rectangle([x, y, x + w, y + h], 5, fill=PANEL,
                        outline=PANEL_LINE, width=1)
    d.rectangle([x + 1, y + 1, x + w - 1, y + 25], fill=ART_BG)
    ART_FUNCS[s["art"]](d, x, y, w, 26)
    num = str(s["disp"])
    f_num = font(SERIF_B, 13)
    nw = tw(d, num, f_num)
    d.rectangle([x + 7, y + 16, x + 13 + nw, y + 32], fill=AMBER)
    d.text((x + 10, y + 17.5), num, font=f_num, fill=INK)
    inner_w = w - 18
    f_place = font(SANS_B, 9)
    tracked(d, (x + 9, y + 33), s["place_label"], f_place, AMBER, 1.2)
    _, hl, tl = card_height(d, s, inner_w)
    f_head = font(SERIF_B, 14.5)
    cy = y + 47
    for line in hl:
        d.text((x + 9, cy), line, font=f_head, fill=CREAM)
        cy += 18
    cy += 3
    f_text = font(SANS, 9.5)
    body = s["text"] + "  - " + s["source"]
    for line in wrap(d, body, f_text, inner_w):
        d.text((x + 9, cy), line, font=f_text, fill=MUTED)
        cy += 11.5


def brief_lines(d, s, col_w):
    """Return (prefix, wrapped body lines) for one brief.

    Every body line sits at the same hanging indent, so all lines
    share the width left over after the prefix.
    """
    f_b = font(SANS, 9.5)
    prefix = f"{s['disp']} {s['place_short']} - "
    body = s["text"] + " (" + s["source"] + ")"
    pw = tw(d, prefix, font(SANS_B, 9.5))
    lines = wrap(d, body, f_b, col_w - 6 - pw)
    return prefix, lines


def render(data):
    img = Image.new("RGB", (W, H), BG_BOT)
    d = ImageDraw.Draw(img)
    for yy in range(H):
        t = yy / H
        col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t)
                    for i in range(3))
        d.line([(0, yy), (W, yy)], fill=col)
    d = ImageDraw.Draw(img)
    x0 = MARGIN
    y = 10

    # masthead
    f_kick = font(str(FONT_DIR / "dejavu" / "DejaVuSans-Bold.ttf"), 10.5)
    tracked(d, (x0, y),
            "◆ ONE DAY ON EARTH - FOLLOW THE SUN · ONE ROTATION OF THE "
            "PLANET", f_kick, CREAM, 1.6)
    tracked(d, (x0 + CW, y), data["kicker_right"], f_kick, CREAM, 1.6,
            anchor_right=True)
    y += 22
    d.line([x0, y, x0 + CW, y], fill=AMBER_DEEP, width=1)
    y += 8
    f_date = font(SERIF_B, 74)
    date_text = data["date_line"]
    dw = tw(d, date_text, f_date)
    d.text(((W - dw) / 2, y), date_text, font=f_date, fill=AMBER)
    y += 90
    f_sub = font(SANS, 11.5)
    sub = (data["census_line"] + " - " + data["region_line"] +
           " - read westward, as the day travelled.")
    sw = tw(d, sub, f_sub)
    d.text(((W - sw) / 2, y), sub, font=f_sub, fill=MUTED)
    y += 19

    # the day in numbers
    f_lab = font(SANS_B, 10)
    tracked(d, (x0, y), "THE DAY IN NUMBERS", f_lab, AMBER, 1.6)
    y += 17
    f_num = font(SERIF_B, 27)
    f_cap = font(SANS, 8.5)
    col_w = CW / 6
    stat_top = y
    for i, st in enumerate(data["stats"]):
        cx = x0 + i * col_w
        d.text((cx + (6 if i else 0), y), st["num"], font=f_num, fill=CREAM)
        cap_lines = wrap(d, st["cap"], f_cap, col_w - 14)
        cy = y + 33
        for line in cap_lines[:2]:
            d.text((cx + (6 if i else 0), cy), line, font=f_cap, fill=MUTED)
            cy += 11
    y = stat_top + 55

    # map
    f_cap2 = font(SANS, 8.5)
    tracked(d, (x0, y),
            "EVERY PIN A STORY - NUMBERED PINS MARK THE DISPATCHES · "
            "DOTS MARK THE BRIEFS · POSITIONS APPROXIMATE", f_cap2, FAINT,
            1.0)
    map_rect = (x0, y + 12, x0 + CW, y + 12 + 76)
    draw_map(d, data, map_rect)
    y = map_rect[3] + 6

    # dispatches
    f_sec = font(SANS_B, 11)
    tracked(d, (x0, y), "DISPATCHES FROM THE DAY", f_sec, AMBER, 1.6)
    right = "the day's biggest stories, told full - numbered in sun order"
    rw = tw(d, right, font(SANS_I, 10.5))
    d.text((x0 + CW - rw, y + 1), right, font=font(SANS_I, 10.5),
           fill=FAINT)
    y += 17
    dispatches = [s for s in data["stories"] if s["kind"] == "dispatch"]
    gap = 8
    card_w = (CW - 3 * gap) // 4
    inner_w = card_w - 18
    rows = [dispatches[i:i + 4] for i in range(0, len(dispatches), 4)]
    for row in rows:
        rh = max(card_height(d, s, inner_w)[0] for s in row)
        for j, s in enumerate(row):
            draw_card(d, s, x0 + j * (card_w + gap), y, card_w, rh)
        y += rh + gap
    y -= gap
    y += 8

    # logbook
    tracked(d, (x0, y), "THE LOGBOOK · BRIEFS FROM THE REST OF THE DAY",
            f_sec, AMBER, 1.6)
    right2 = "first light · midday · dusk - still in sun order"
    rw2 = tw(d, right2, font(SANS_I, 10.5))
    d.text((x0 + CW - rw2, y + 1), right2, font=font(SANS_I, 10.5),
           fill=FAINT)
    y += 17
    briefs = [s for s in data["stories"] if s["kind"] == "brief"]
    leg_titles = {l["leg"]: l["title"] for l in data["legs"]}
    col_gap = 24
    col_w = (CW - col_gap) / 2
    f_leg = font(SANS_B, 9.5)
    f_pre = font(SANS_B, 9.5)
    f_b = font(SANS, 9.5)
    pitch = 11

    def draw_leg_block(top, legs_wanted):
        cy = top
        for leg_no in legs_wanted:
            tracked(d, (x0 + (0 if leg_no == 1 else col_w + col_gap), cy),
                    leg_titles[leg_no], f_leg, SKY, 1.0)
            cy += 12.5
            for s in [b for b in briefs if b["leg"] == leg_no]:
                prefix, lines = brief_lines(d, s, col_w)
                bx = x0 + (0 if leg_no == 1 else col_w + col_gap)
                d.text((bx, cy), prefix, font=f_pre, fill=AMBER)
                pw = tw(d, prefix, f_pre)
                ly = cy
                for k, line in enumerate(lines):
                    lx = bx + (pw if k == 0 else pw)
                    d.text((lx, ly), line, font=f_b, fill=CREAM)
                    ly += pitch
                cy = ly + 2
        return cy

    left_bottom = draw_leg_block(y, [1])
    # right column legs drawn with same routine offset: emulate by
    # re-running with column shift baked into leg numbers 2 and 3
    right_bottom = draw_leg_block(y, [2, 3])
    y = max(left_bottom, right_bottom) + 4

    # cutting-room box
    box_y = y
    f_bt = font(SANS_B, 9.5)
    f_bi = font(SANS, 9.5)
    items_text = " · ".join(data["box_items"])
    item_lines = wrap(d, items_text, f_bi, CW - 24)
    box_h = 12 + 14 + len(item_lines) * 12 + 6
    d.rounded_rectangle([x0, box_y, x0 + CW, box_y + box_h], 5,
                        fill=(11, 22, 40), outline=AMBER_DEEP, width=1)
    tracked(d, (x0 + 12, box_y + 9), data["box_title"], f_bt, AMBER, 0.8)
    iy = box_y + 25
    for line in item_lines:
        d.text((x0 + 12, iy), line, font=f_bi, fill=CREAM)
        iy += 12
    y = box_y + box_h + 7

    # footer
    f_foot = font(SANS, 9.5)
    aw = tw(d, data["attestation"], f_foot)
    d.text(((W - aw) / 2, y), data["attestation"], font=f_foot, fill=CREAM)
    y += 12
    f_src = font(SANS, 8.5)
    sw2 = tw(d, data["sources_line"], f_src)
    d.text(((W - sw2) / 2, y), data["sources_line"], font=f_src, fill=FAINT)
    y += 13
    print("page bottom:", y)
    return img


def main():
    data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))
    img = render(data)
    out = HERE / "entry.png"
    img.save(out, format="PNG", optimize=True)
    size = out.stat().st_size
    print("entry.png bytes:", size)
    if size > 350_000:
        q = img.quantize(colors=256, method=Image.MEDIANCUT)
        q.save(out, format="PNG", optimize=True)
        print("quantized to 256 colours, bytes:", out.stat().st_size)


if __name__ == "__main__":
    main()
