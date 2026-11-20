#!/usr/bin/env python3
"""Evening renderer for news-image-20261120 (slot 2 revision).

Fresh implementation written in-session for the 46-record evening set
(43 distinct stories printed; three morning stories updated in place
by their evening successors). Draws a 1024x1024 cream broadsheet:
big Friday date, stat band, 16 dispatch cards (36px condensed-bold
headlines), 27 one-line briefs, and a dark high-contrast held-back
box at 24px. Local-only tool: the shipped entry.png is copied by
main.py at grade time. Requires Pillow locally.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W = 1024
MX = 14
CW = W - 2 * MX

BG = (246, 241, 227)        # cream paper
CARD = (255, 253, 246)      # card face
INK = (22, 30, 44)          # near-black blue ink
MUTE = (84, 92, 108)        # secondary ink
ACCENT = (164, 22, 35)      # crimson
GOLD = (146, 106, 18)       # dark gold for rules/labels
BOXBG = (22, 30, 44)        # held-back box: dark
BOXFG = (246, 241, 227)     # held-back box: cream on dark
BOXHEAD = (255, 205, 92)    # box heading amber on dark

NOTO = "/usr/share/fonts/truetype/noto"
F_BOLD = f"{NOTO}/NotoSans-Bold.ttf"
F_REG = f"{NOTO}/NotoSans-Regular.ttf"
F_CB = f"{NOTO}/NotoSans-CondensedBold.ttf"
F_CR = f"{NOTO}/NotoSans-Condensed.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if draw.textlength(t, font=fnt) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def main():
    data = json.loads((HERE / "data.json").read_text())
    img = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(img)

    dispatches = [s for s in data["stories"] if s["kind"] == "dispatch"]
    briefs = [s for s in data["stories"] if s["kind"] == "brief"]

    y = 6
    # --- kicker row -------------------------------------------------
    fk = font(F_BOLD, 13)
    d.text((MX, y), "ONE DAY ON EARTH - THE WORLD IN ONE DAY", font=fk, fill=INK)
    right = "ONE PAGE - EVERY STORY FRIDAY'S"
    d.text((W - MX - d.textlength(right, font=fk), y), right, font=fk, fill=ACCENT)
    y += 16
    d.line([(MX, y), (W - MX, y)], fill=INK, width=3)
    y += 4

    # --- the date, largest type on the page (48px) -------------------
    fd = font(F_BOLD, 48)
    d.text((MX, y), "FRIDAY 20 NOVEMBER 2026", font=fd, fill=INK)
    y += 50

    # --- census / attestation line ----------------------------------
    fc = font(F_REG, 15)
    d.text((MX, y), data["census_line"], font=fc, fill=MUTE)
    y += 20
    d.line([(MX, y), (W - MX, y)], fill=GOLD, width=2)
    y += 5

    # --- stat band ----------------------------------------------------
    stats = data["stats"]
    colw = CW / len(stats)
    fn = font(F_BOLD, 22)
    fcap = font(F_REG, 11)
    for i, s in enumerate(stats):
        x = MX + i * colw
        d.text((x, y), s["num"], font=fn, fill=ACCENT if i % 2 == 0 else INK)
        assert len(wrap(d, s["cap"], fcap, colw - 8)) == 1, s["cap"]
        d.text((x, y + 25), s["cap"], font=fcap, fill=MUTE)
    y += 40

    # --- dispatches ---------------------------------------------------
    fh_sec = font(F_CB, 18)
    d.text((MX, y), "DISPATCHES - FRIDAY 20 NOVEMBER 2026, TOLD IN FULL - NUMBERED IN SUN ORDER", font=fh_sec, fill=INK)
    y += 23

    cols = 4
    gap = 3
    cardw = (CW - (cols - 1) * gap) / cols
    fplace = font(F_CB, 14)
    fhead = font(F_CB, 36)
    ffact = font(F_BOLD, 14)
    row_h = 112
    rows = [dispatches[i:i + cols] for i in range(0, len(dispatches), cols)]
    for row in rows:
        for j, s in enumerate(row):
            x = MX + j * (cardw + gap)
            hl = wrap(d, s["headline"], fhead, cardw - 14)
            assert len(hl) <= 2, (s["disp"], hl)
            assert d.textlength(s["place_label"], font=fplace) <= cardw - 14
            assert d.textlength(s["fact"], font=ffact) <= cardw - 14
            d.rectangle([x, y, x + cardw, y + row_h], fill=CARD, outline=INK, width=1)
            d.rectangle([x, y, x + cardw, y + 3], fill=ACCENT)
            d.text((x + 7, y + 6), s["place_label"], font=fplace, fill=GOLD)
            hy = y + 24
            for ln in hl:
                d.text((x + 7, hy), ln, font=fhead, fill=INK)
                hy += 32
            d.text((x + 7, y + 96), s["fact"], font=ffact, fill=ACCENT)
        y += row_h + gap
    y -= gap
    y += 4

    # --- briefs -------------------------------------------------------
    d.text((MX, y), "ALSO ON FRIDAY 20 NOVEMBER - THE REST OF THE DAY IN BRIEF", font=fh_sec, fill=INK)
    y += 17
    fbr = font(F_REG, 15)
    fbnum = font(F_BOLD, 15)
    half = (len(briefs) + 1) // 2
    col2x = MX + CW / 2 + 6
    colw2 = CW / 2 - 6
    for idx, s in enumerate(briefs):
        col = 0 if idx < half else 1
        r = idx if col == 0 else idx - half
        x = MX if col == 0 else col2x
        by = y + r * 15.0
        num = f"{s['disp']}"
        d.text((x, by), num, font=fbnum, fill=ACCENT)
        nw = d.textlength(num, font=fbnum) + 5
        line = f"{s['place_short']} - {s['text']}"
        assert d.textlength(line, font=fbr) <= colw2 - nw, f"brief too wide: {line}"
        d.text((x + nw, by), line, font=fbr, fill=INK)
    y += int(half * 15.0) + 5

    # --- held-back box (dark, high contrast, items 24px) --------------
    box_top = y
    fboxh = font(F_CB, 25)
    fbox = font(F_CR, 24)
    items_text = "  ·  ".join(data["box_items"])
    box_lines = wrap(d, items_text, fbox, CW - 28)
    box_h = 5 + 24 + int(len(box_lines) * 22.5) + 5
    d.rectangle([MX, box_top, W - MX, box_top + box_h], fill=BOXBG)
    d.text((MX + 14, box_top + 7), data["box_title"], font=fboxh, fill=BOXHEAD)
    by = box_top + 29
    for ln in box_lines:
        d.text((MX + 14, by), ln, font=fbox, fill=BOXFG)
        by += 22.5
    y = box_top + box_h + 5

    # --- footer -------------------------------------------------------
    ff = font(F_REG, 12)
    d.text((MX, y), data["sources_line"], font=ff, fill=MUTE)
    y += 14
    print(f"final y = {y} (limit 1024), box lines = {len(box_lines)}")
    assert y <= W, "layout overflow"

    out = img.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    out.save(HERE / "entry.png", optimize=True)
    print("saved entry.png")


if __name__ == "__main__":
    main()
