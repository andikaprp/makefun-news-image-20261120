#!/usr/bin/env python3
"""One Day on Earth - Friday 20 November 2026 - slot-3 candidate v2 renderer.

Original renderer authored for the v2 page: v1's observatory skeleton
(~90px-class date, strap, stat band, region strip, sun-path chart)
merged with the slot-2 page's headlined breadth (3 illustrated leads
+ 13 dispatch cards at 36px headline size + numbered briefs + the
18-item DATE CHECK box). Reads data_saturday2.json; writes entry.png
(1024x1024) and 512/300 Lanczos renders. Deterministic.
A "|" inside a dispatch headline marks the intended line break.
The 13th dispatch runs wide (one headline line) beside the chart
panel in the grid's last row.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data_saturday2.json")

W = 1024
MX = 20
CW = W - 2 * MX

NAVY = (13, 27, 46)
NAVY2 = (22, 41, 66)
CREAM = (246, 239, 221)
CARD = (252, 248, 238)
INK = (18, 30, 52)
AMBER = (233, 164, 62)
CRIMSON = (178, 47, 42)
TEAL = (96, 178, 178)
FAINT = (52, 74, 104)
STRAPC = (238, 226, 198)

FD = "/usr/share/fonts/truetype/noto/"
F_DATE = FD + "NotoSansDisplay-ExtraCondensedBold.ttf"
F_COND_B = FD + "NotoSans-CondensedBold.ttf"
F_COND = FD + "NotoSans-Condensed.ttf"
F_COND_I = FD + "NotoSans-CondensedItalic.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


PROBLEMS = []


def draw_line(dr, x, y_top, text, fnt, fill, tracking=0):
    """Draw one line with ink top at y_top; return ink height."""
    bbox = dr.textbbox((0, 0), text, font=fnt)
    if tracking:
        cx = x
        for ch in text:
            cb = dr.textbbox((0, 0), ch, font=fnt)
            dr.text((cx - cb[0], y_top - bbox[1]), ch, font=fnt, fill=fill)
            cx += dr.textlength(ch, font=fnt) + tracking
        return bbox[3] - bbox[1]
    dr.text((x - bbox[0], y_top - bbox[1]), text, font=fnt, fill=fill)
    return bbox[3] - bbox[1]


def ink_h(dr, text, fnt):
    bb = dr.textbbox((0, 0), text, font=fnt)
    return bb[3] - bb[1]


def wrap(dr, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if dr.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def check_fit(dr, text, fnt, max_w, what):
    wdt = dr.textlength(text, font=fnt)
    if wdt > max_w:
        PROBLEMS.append(f"OVERFLOW {what}: {wdt:.0f} > {max_w} :: {text!r}")
    return wdt


def headline_lines(dr, text, fnt, max_w, what):
    if "|" in text:
        lines = [p.strip() for p in text.split("|")]
        for ln in lines:
            check_fit(dr, ln, fnt, max_w, what)
        return lines
    return wrap(dr, text, fnt, max_w)


# ---------------------------------------------------------------- art
def art_kyiv(dr, x, y, w, h):
    dr.rectangle([x, y, x + w, y + h], fill=NAVY2)
    for i in range(5):
        sx = x + 16 + i * 54
        dr.arc([sx, y - 8, sx + 118, y + h + 22], start=200, end=320,
               fill=AMBER, width=2)
        dr.ellipse([sx + 95, y + h - 7, sx + 100, y + h - 2], fill=CRIMSON)
    dr.ellipse([x + w - 22, y + 3, x + w - 12, y + 13], fill=AMBER)


def art_akvan(dr, x, y, w, h):
    dr.rectangle([x, y, x + w, y + h], fill=NAVY2)
    cx, cy = x + w // 2, y + h // 2
    pts = []
    for t in range(0, 88):
        ang = t * 0.42
        r = 1.2 + t * 0.115
        pts.append((cx + r * math.cos(ang) * 2.9, cy + r * math.sin(ang) * 0.58))
    dr.line(pts, fill=TEAL, width=2)
    dr.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=AMBER)


def art_selloff(dr, x, y, w, h):
    dr.rectangle([x, y, x + w, y + h], fill=NAVY2)
    for gy in (4, 9, 14):
        dr.line([x + 8, y + gy, x + w - 8, y + gy], fill=FAINT, width=1)
    pts = [(x + 14 + i * (w - 40) / 5, y + 2 + i * 2.7) for i in range(6)]
    dr.line(pts, fill=CRIMSON, width=2)
    for px, py in pts:
        dr.ellipse([px - 2, py - 2, px + 2, py + 2], fill=AMBER)


ART = {"kyiv": art_kyiv, "akvan": art_akvan, "selloff": art_selloff}


# ---------------------------------------------------------------- zones
def masthead(dr, d):
    y = 6
    f_kick = font(F_COND_B, 15)
    y += draw_line(dr, MX, y, d["kicker"], f_kick, AMBER, tracking=2) + 3
    f_date = font(F_DATE, 84)
    wd = sum(dr.textlength(c, font=f_date) + 1 for c in d["day"])
    if wd > CW + 6:
        PROBLEMS.append(f"OVERFLOW date: {wd:.0f}")
    y += draw_line(dr, MX - 2, y, d["day"], f_date, CREAM, tracking=1) + 5
    f_strap = font(F_COND_I, 21)
    check_fit(dr, d["strap"], f_strap, CW, "strap")
    y += draw_line(dr, MX, y, d["strap"], f_strap, STRAPC) + 5
    # stat band: value over label, one column per stat
    dr.line([MX, y, MX + CW, y], fill=AMBER, width=2)
    y += 4
    f_val = font(F_COND_B, 25)
    f_lab = font(F_COND_B, 10)
    colw = CW / 6.0
    val_h = 0
    for i, s in enumerate(d["stats"]):
        cx = MX + i * colw
        val_h = max(val_h, draw_line(dr, cx, y, s["value"], f_val, CREAM))
        check_fit(dr, s["value"], f_val, colw - 6, f"stat value {i}")
    y += val_h + 1
    lab_h = 0
    for i, s in enumerate(d["stats"]):
        cx = MX + i * colw
        lab_h = max(lab_h, draw_line(dr, cx, y, s["label"], f_lab, AMBER))
        check_fit(dr, s["label"], f_lab, colw - 4, f"stat label {i}")
    y += lab_h + 4
    dr.line([MX, y, MX + CW, y], fill=AMBER, width=2)
    y += 4
    dr.rectangle([0, y, W, y + 23], fill=NAVY2)
    f_reg = font(F_COND_B, 18)
    line = "   ".join(["THE DAY IN REGIONS:"] +
                      [f"{r['name']} {r['count']}" for r in d["regions"]])
    draw_line(dr, MX, y + 2, line, f_reg, AMBER)
    check_fit(dr, line, f_reg, CW, "region strip")
    y += 23
    return y


def lead_card(dr, x, y, w, h, lead):
    dr.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=2)
    art_h = 18
    ART[lead["art"]](dr, x + 2, y + 2, w - 4, art_h)
    f_chip = font(F_COND_B, 11)
    src = lead["source"]
    sw = dr.textlength(src, font=f_chip)
    dr.rectangle([x + w - sw - 12, y + 3, x + w - 4, y + 17], fill=NAVY)
    draw_line(dr, x + w - sw - 8, y + 4, src, f_chip, CREAM)
    cy = y + 2 + art_h + 4
    f_place = font(F_COND_B, 13)
    cy += draw_line(dr, x + 9, cy, lead["place"], f_place, CRIMSON) + 2
    f_head = font(F_COND_B, 37)
    lines = headline_lines(dr, lead["headline"], f_head, w - 18, "lead headline")
    if len(lines) > 2:
        PROBLEMS.append(f"LEAD headline >2 lines: {lead['headline']!r}")
    for ln in lines:
        draw_line(dr, x + 9, cy, ln, f_head, INK)
        cy += 34
    f_fact = font(F_COND_B, 15)
    fl = wrap(dr, lead["fact"], f_fact, w - 18)
    if len(fl) > 1:
        PROBLEMS.append(f"LEAD fact wraps: {lead['fact']!r}")
    cy += draw_line(dr, x + 9, cy, lead["fact"], f_fact, CRIMSON) + 2
    f_sum = font(F_COND, 14)
    sl = wrap(dr, lead["summary"], f_sum, w - 18)
    if len(sl) > 2:
        PROBLEMS.append(f"LEAD summary >2 lines: {lead['summary']!r}")
    for ln in sl:
        cy += draw_line(dr, x + 9, cy, ln, f_sum, INK) + 1
    if cy > y + h:
        PROBLEMS.append(f"LEAD content {cy - y:.0f} > height {h}: {lead['headline']!r}")
    return cy - y


def dispatch_card(dr, x, y, w, h, num, disp):
    dr.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    dr.rectangle([x, y, x + 4, y + h], fill=CRIMSON)
    f_place = font(F_COND_B, 12)
    f_src = font(F_COND, 11)
    left = f"{num} · {disp['place']}"
    sw = dr.textlength(disp["source"], font=f_src)
    check_fit(dr, left, f_place, w - 22 - sw, f"dispatch place {num}")
    draw_line(dr, x + 10, y + 4, left, f_place, CRIMSON)
    draw_line(dr, x + w - 8 - sw, y + 5, disp["source"], f_src, INK)
    cy = y + 4 + 12
    f_head = font(F_COND_B, 36)
    lines = headline_lines(dr, disp["headline"], f_head, w - 18, f"dispatch headline {num}")
    if len(lines) != 2:
        PROBLEMS.append(f"DISPATCH headline {len(lines)} lines (want 2): {disp['headline']!r}")
    for ln in lines:
        draw_line(dr, x + 10, cy, ln, f_head, INK)
        cy += 33
    f_fact = font(F_COND_B, 14)
    check_fit(dr, disp["fact"], f_fact, w - 18, f"dispatch fact {num}")
    draw_line(dr, x + 10, cy, disp["fact"], f_fact, CRIMSON)
    if cy + 11 > y + h:
        PROBLEMS.append(f"DISPATCH content exceeds card {num}")


def wide_dispatch(dr, x, y, w, h, num, disp):
    dr.rectangle([x, y, x + w, y + h], fill=CARD, outline=INK, width=1)
    dr.rectangle([x, y, x + 4, y + h], fill=CRIMSON)
    f_place = font(F_COND_B, 12)
    f_src = font(F_COND, 11)
    left = f"{num} · {disp['place']}"
    sw = dr.textlength(disp["source"], font=f_src)
    draw_line(dr, x + 10, y + 3, left, f_place, CRIMSON)
    draw_line(dr, x + w - 8 - sw, y + 4, disp["source"], f_src, INK)
    cy = y + 3 + 11
    f_head = font(F_COND_B, 36)
    text = disp["headline"].replace("|", " ")
    lines = wrap(dr, text, f_head, w - 18)
    if len(lines) != 1:
        PROBLEMS.append(f"WIDE headline {len(lines)} lines (want 1): {text!r}")
    draw_line(dr, x + 10, cy, text, f_head, INK)
    cy += 27  # cap-height advance: the 'g' descender sits clear of the fact line's span
    f_fact = font(F_COND_B, 14)
    check_fit(dr, disp["fact"], f_fact, w - 18, "wide fact")
    draw_line(dr, x + 10, cy, disp["fact"], f_fact, CRIMSON)


def chart_panel(dr, x, y, w, h, d):
    dr.rectangle([x, y, x + w, y + h], fill=NAVY, outline=INK, width=1)
    f_cap = font(F_COND_B, 11)
    draw_line(dr, x + 10, y + 3, d["chart_caption"], f_cap, AMBER)
    check_fit(dr, d["chart_caption"], f_cap, w - 20, "chart caption")
    px0, py0 = x + 12, y + 17
    pw, ph = w - 24, h - 21
    gx = px0
    while gx < px0 + pw:
        gy = py0
        while gy < py0 + ph:
            dr.ellipse([gx, gy, gx + 1.5, gy + 1.5], fill=FAINT)
            gy += 11
        gx += 11
    pts = []
    for i in range(61):
        t = i / 60.0
        pts.append((px0 + t * pw, py0 + ph * 0.55 - math.sin(t * math.pi) * ph * 0.34))
    dr.line(pts, fill=AMBER, width=1)
    for p in d["pins"]:
        X = px0 + (p["lon"] + 175) / 355.0 * pw
        Y = py0 + (72 - p["lat"]) / 132.0 * ph
        dr.ellipse([X - 2.2, Y - 2.2, X + 2.2, Y + 2.2], fill=AMBER, outline=NAVY)


def briefs_block(dr, y, d):
    f_head = font(F_COND_B, 16)
    draw_line(dr, MX, y, d["briefs_heading"], f_head, INK)
    check_fit(dr, d["briefs_heading"], f_head, CW, "briefs heading")
    y += 13 + 3
    f_num = font(F_COND_B, 12)
    f_place = font(F_COND_B, 12)
    f_txt = font(F_COND, 12)
    colw = (CW - 14) / 2.0
    rows = (len(d["briefs"]) + 1) // 2
    lh = 11.2
    for r in range(rows):
        for c in range(2):
            idx = r * 2 + c
            if idx >= len(d["briefs"]):
                break
            b = d["briefs"][idx]
            x = MX + c * (colw + 14)
            by = y + r * lh
            draw_line(dr, x, by, f"{idx + 1:02d}", f_num, CRIMSON)
            tx = x + 22
            draw_line(dr, tx, by, b["place"], f_place, INK)
            pw_ = dr.textlength(b["place"], font=f_place)
            seg = f"— {b['text']} ({b['source']})"
            draw_line(dr, tx + pw_ + 4, by, seg, f_txt, INK)
            check_fit(dr, seg, f_txt, colw - 26 - pw_, f"brief {idx + 1}")
    return y + rows * lh


def box_block(dr, y, d):
    f_head = font(F_COND_B, 25)
    f_item = font(F_COND, 24)
    text = " · ".join(d["held_back"])
    lines = wrap(dr, text, f_item, CW - 24)
    head_h = ink_h(dr, d["held_back_heading"], f_head)
    box_h = 5 + head_h + 3 + 20 * len(lines) + 5
    dr.rectangle([MX, y, MX + CW, y + box_h], fill=NAVY)
    draw_line(dr, MX + 12, y + 5, d["held_back_heading"], f_head, AMBER)
    check_fit(dr, d["held_back_heading"], f_head, CW - 24, "box heading")
    cy = y + 5 + head_h + 3
    for ln in lines:
        draw_line(dr, MX + 12, cy, ln, f_item, CREAM)
        cy += 20
    return box_h, len(lines)


def main():
    d = json.load(open(DATA))
    scratch = Image.new("RGB", (W, W), CREAM)
    mast_bottom = masthead(ImageDraw.Draw(scratch), d)
    PROBLEMS.clear()

    img = Image.new("RGB", (W, W), CREAM)
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, W, mast_bottom], fill=NAVY)
    masthead(dr, d)
    print(f"masthead: 0..{mast_bottom}")
    y = mast_bottom + 5

    lead_h = 140
    lw = (CW - 20) / 3.0
    used = 0
    for i, lead in enumerate(d["leads"]):
        used = max(used, lead_card(dr, MX + i * (lw + 10), y, lw, lead_h, lead))
    print(f"leads: {y}..{y + lead_h} (content {used:.0f})")
    y += lead_h + 4

    card_h, gap = 94, 5
    dw = (CW - 3 * gap) / 4.0
    for r in range(3):
        gy = y + r * (card_h + gap)
        for c in range(4):
            idx = r * 4 + c
            dispatch_card(dr, MX + c * (dw + gap), gy, dw, card_h,
                          idx + 1, d["dispatches"][idx])
    last_y = y + 3 * (card_h + gap)
    wide_w = 2 * dw + gap
    wide_dispatch(dr, MX, last_y, wide_w, 56, 13, d["dispatches"][12])
    chart_panel(dr, MX + wide_w + gap, last_y, CW - wide_w - gap, 56, d)
    grid_h = 3 * (card_h + gap) + 56
    print(f"grid: {y}..{y + grid_h}")
    y += grid_h + 4

    yb = briefs_block(dr, y, d)
    print(f"briefs: {y}..{yb}")
    y = yb + 4

    box_h, nlines = box_block(dr, y, d)
    print(f"box: {y}..{y + box_h} ({nlines} item lines)")
    y += box_h + 4

    f_foot = font(F_COND, 12)
    fl = wrap(dr, d["footer"], f_foot, CW)
    if len(fl) > 1:
        PROBLEMS.append(f"footer {len(fl)} lines (want 1)")
    for ln in fl:
        y += draw_line(dr, MX, y, ln, f_foot, INK) + 2
    print(f"TOTAL HEIGHT USED: {y:.0f} / 1024")
    if y > 1024:
        PROBLEMS.append(f"PAGE OVERFLOW: total {y:.0f} > 1024")
    if PROBLEMS:
        print("PROBLEMS:")
        for p in PROBLEMS:
            print(" -", p)
    else:
        print("ALL FIT CHECKS PASSED")

    out = os.path.join(HERE, "entry.png")
    pal = img.convert("P", palette=Image.ADAPTIVE, colors=96)
    pal.save(out, optimize=True)
    print("entry.png bytes:", os.path.getsize(out))
    img.resize((512, 512), Image.LANCZOS).save(os.path.join(HERE, "entry-512.png"))
    img.resize((300, 300), Image.LANCZOS).save(os.path.join(HERE, "entry-300.png"))
    return 0 if not PROBLEMS else 1


if __name__ == "__main__":
    sys.exit(main())
