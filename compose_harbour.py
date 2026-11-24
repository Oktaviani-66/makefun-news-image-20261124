#!/usr/bin/env python3
"""THE HARBOUR LIGHT - NI24 entry renderer (Akun 13, written fresh this session).
Renders a one-day newspaper front page for Tuesday 24 November 2026 at 3000x3000,
then downscales to 1024x1024 and quantizes to 256 colours.
Stdlib + Pillow at BUILD time only; the submitted program (main.py) is a
stdlib-only copy of the finished entry.png.
All facts come from ni24-pool.md + ni24-pool-refresh-0700.md (locked pool).
"""
import argparse
import sys
from PIL import Image, ImageDraw, ImageFont

W = 3000
M = 70
CW = W - 2 * M

TEAL_D = (10, 58, 55)
TEAL = (14, 107, 100)
TEAL_L = (217, 237, 234)
TEAL_M = (120, 180, 174)
PAPER = (253, 252, 247)
INK = (20, 32, 31)
GREY = (90, 100, 98)
RED = (166, 30, 30)
RED_L = (250, 230, 228)
GOLD = (196, 154, 60)
WHITE = (255, 255, 255)
BLACK = (12, 18, 17)

REGION_COLORS = {
    "EUROPE": (14, 107, 100),
    "MIDDLE EAST": (138, 90, 0),
    "AMERICAS": (31, 78, 121),
    "ASIA-PACIFIC": (123, 31, 162),
    "WORLD": (85, 85, 85),
    "OCEANIA": (46, 125, 50),
    "AFRICA": (179, 84, 30),
}

F_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
F_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, int(size))


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, max_w, fill, leading=None, max_lines=None):
    lines = wrap(draw, text, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading or int(fnt.size * 1.22)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def scene(draw, box, kind, sky, ground, accent):
    """Flat layered illustration strip filling the whole box (data-bearing art).
    Drawn on a temp layer so nothing can spill outside the strip."""
    x0, y0, x1, y1 = box
    sh = y1 - y0
    sw = x1 - x0
    layer = Image.new("RGB", (sw, sh), sky)
    ld = ImageDraw.Draw(layer)
    # sun / moon disc
    r = max(14, sh // 4)
    ld.ellipse([sw - r - 20, 10, sw - 20, 10 + 2 * r], fill=accent)
    # distant skyline / hills
    n = 5
    bw = sw // n
    gh = sh // 3
    for i in range(n):
        h = 10 + ((i * 53) % max(8, gh - 12))
        ld.rectangle([i * bw + 6, sh - gh - h, (i + 1) * bw - 6, sh - gh],
                     fill=tuple(max(0, c - 25) for c in sky))
    ld.rectangle([0, sh - gh, sw, sh], fill=ground)
    if kind == "sea":
        for j, yy in enumerate(range(sh - gh + 5, sh - 6, max(10, gh // 3))):
            off = 22 if j % 2 else 0
            for xx in range(-30 + off, sw, 96):
                ld.arc([xx, yy, xx + 66, yy + 22], 0, 180, fill=WHITE, width=4)
        # ship hull + funnel
        hy = sh - gh - 5
        ld.polygon([(50, hy - 28), (250, hy - 28), (225, hy + 5),
                    (75, hy + 5)], fill=BLACK)
        ld.rectangle([125, hy - 54, (125 + 30), hy - 28], fill=RED)
    elif kind == "city":
        for i in range(6):
            bx = 12 + i * ((sw - 24) // 6)
            bh = 22 + ((i * 67) % max(10, sh - 50))
            ld.rectangle([bx, sh - gh - bh, bx + 44, sh - gh], fill=BLACK)
            for wy in range(sh - gh - bh + 8, sh - gh - 6, 22):
                ld.rectangle([bx + 8, wy, bx + 19, wy + 10], fill=(255, 214, 90))
    elif kind == "flame":
        cx = sw // 3
        for i, rr in enumerate((int(sh * 0.30), int(sh * 0.22), int(sh * 0.14), int(sh * 0.08))):
            ld.ellipse([cx - rr, sh - gh - rr * 2 + i * 3,
                        cx + rr, sh - gh + i * 3],
                       fill=(255, 120 + i * 20, 30) if i < 2 else (255, 205, 60))
    elif kind == "chart":
        pts = [(20, sh - 24), (int(sw * .25), sh - gh - 24),
               (int(sw * .45), sh - gh + 5), (int(sw * .65), sh - gh - 38),
               (int(sw * .85), sh - 36), (sw - 20, sh - gh - 16)]
        ld.line(pts, fill=accent, width=8, joint="curve")
        for p in pts:
            ld.ellipse([p[0] - 8, p[1] - 8, p[0] + 8, p[1] + 8], fill=RED)
    elif kind == "court":
        ld.ellipse([30, 8, sw - 30, sh - gh - 6], outline=WHITE, width=5)
        ld.line([sw // 2, 8, sw // 2, sh - gh - 6], fill=WHITE, width=5)
        ld.ellipse([sw // 2 - 16, sh - gh - 32, sw // 2 + 16, sh - gh],
                   fill=(255, 140, 40))
    elif kind == "dome":
        ld.pieslice([sw // 4, 4, 3 * sw // 4, sh // 2 + 16], 180, 360, fill=accent)
        ld.rectangle([sw // 4, sh // 4, 3 * sw // 4, sh - gh], fill=BLACK)
        for wx in range(sw // 4 + 10, 3 * sw // 4 - 16, 38):
            ld.rectangle([wx, sh // 4 + 10, wx + 19, sh // 4 + 38], fill=(255, 214, 90))
    # data band at the bottom of the strip
    ld.rectangle([0, sh - 26, sw, sh], fill=accent)
    draw._image.paste(layer, (x0, y0))


# ---------------------------------------------------------------- cards
# (num, region, place, headline, deck, chip, sources, first_reported, scene, sky, ground, accent)
CARDS = [
    (1, "EUROPE", "KYIV REGION, UKRAINE",
     "Kyiv strikes kill at least 15",
     "11 killed in a Dymer block of flats; 5 hurt in Kyiv.",
     "15 KILLED \u00b7 11 IN DYMER", "Times / AP", "23 Nov", "city",
     (226, 232, 228), (70, 80, 78), RED),
    (2, "EUROPE", "GULF OF FINLAND",
     "Russian cargo ship Sparta II hit, towed clear",
     "All 16 crew got off; towed out on Sunday night.",
     "16 CREW SAFE \u00b7 TOWED OUT", "Reuters / Times / WSJ", "22\u201323 Nov", "sea",
     (178, 214, 220), (30, 70, 90), TEAL),
    (3, "MIDDLE EAST", "WASHINGTON",
     "US sanctions about 30 Iran-linked exchange houses",
     "Iran sanctions target the shadow-banking core.",
     "\u223c30 SANCTIONED", "AP / Treasury", "23 Nov", "chart",
     (238, 226, 200), (90, 80, 50), (138, 90, 0)),
    (4, "EUROPE", "BENGHAZI, LIBYA",
     "Ukraine sinks warship Merkury",
     "7 sea drones launched; Ka-27 destroyed.",
     "7 SEA DRONES \u00b7 MERKURY SUNK", "CNN / Times / WSJ / AP", "23 Nov", "sea",
     (20, 60, 70), (10, 40, 50), (255, 120, 40)),
    (5, "WORLD", "ANTALYA, T\u00dcRKIYE",
     "COP31 ends with no deal",
     "Antalya Pact falls; fossil fuels dropped.",
     "NO DEAL \u00b7 FIRST SINCE 2000", "Times / Guardian", "22\u201323 Nov", "flame",
     (240, 220, 180), (60, 55, 40), (200, 90, 20)),
    (6, "MIDDLE EAST", "GAZA CITY",
     "Israeli strikes kill 3 in Gaza",
     "3 killed on Monday, incl. a UNRWA employee.",
     "3 KILLED", "AP", "23 Nov", "city",
     (230, 225, 215), (80, 75, 70), (120, 90, 60)),
    (7, "MIDDLE EAST", "WESTERN YEMEN",
     "Strike kills 11 in western Yemen",
     "Houthis say 11 killed, 19 wounded Monday.",
     "11 KILLED \u00b7 19 WOUNDED", "AP", "23 Nov", "city",
     (235, 220, 200), (95, 70, 45), (160, 60, 30)),
    (8, "AMERICAS", "NEW YORK",
     "Huang back as Nvidia CEO",
     "Reinstated Monday; shares rose 31%.",
     "+31% \u00b7 HUANG BACK", "Reuters", "23 Nov", "chart",
     (200, 230, 210), (20, 90, 60), (30, 160, 90)),
    (9, "AMERICAS", "MARKETS",
     "Gold rebounds 1.5% to $3,588",
     "Bullion rose after its worst week in 8 months.",
     "$3,588/OZ \u00b7 +1.5%", "Reuters", "23 Nov", "chart",
     (245, 225, 170), (120, 100, 40), GOLD),
    (10, "WORLD", "CRYPTO",
     "Bitcoin steadies near $61,284",
     "$61,284 at 12:52 UTC; Kraken trades stand.",
     "$61,284", "CoinPaprika", "23 Nov", "chart",
     (210, 220, 235), (40, 60, 90), (31, 78, 121)),
    (11, "AMERICAS", "LOS ANGELES",
     "GTA VI takes $3.8bn day one",
     "Biggest entertainment launch on record.",
     "$3.8BN DAY ONE", "ActiveInvestorMag", "23 Nov", "flame",
     (235, 200, 220), (80, 30, 60), (200, 40, 90)),
    (12, "EUROPE", "LIVERPOOL",
     "Liverpool 4\u20130 Man Utd",
     "Pochettino\u2019s debut: Yoro off, United 19th.",
     "4\u20130", "Mint / NextSportsWeb", "23 Nov", "court",
     (220, 235, 225), (25, 90, 50), (30, 140, 60)),
    (13, "AMERICAS", "WASHINGTON",
     "Democrats take both chambers",
     "Democrats 258; Van Hollen v Schumer 1 Dec.",
     "258\u2013173", "BBC / ActiveInvestorMag", "23 Nov", "dome",
     (215, 225, 240), (35, 55, 85), (31, 78, 121)),
    (14, "OCEANIA", "WELLINGTON",
     "NZ bat out draw with India",
     "Mitchell 49*, Phillips 26* in the draw.",
     "DRAW \u00b7 239/5", "HS / WicketPulse", "23 Nov", "court",
     (225, 235, 220), (45, 85, 55), (40, 130, 70)),
]

# ---------------------------------------------------------------- briefs (ALSO ON, numbered 15..36)
# (region, text, source)
BRIEFS = [
    ("ASIA-PACIFIC", "N. Korea weighs shutting Swiss office \u2014 KCNA", "Reuters"),
    ("AFRICA", "Congo halts cobalt exports from 30 Nov", "Reuters"),
    ("ASIA-PACIFIC", "Indonesia: 24 killed in a factory blaze", "Reuters"),
    ("AMERICAS", "CrowdStrike buys Zscaler in a $44bn deal", "Reuters"),
    ("AMERICAS", "Trump hosts gala for meme-coin investors", "Reuters"),
    ("AMERICAS", "US Army to detonate lead stockpile in Iowa", "Reuters"),
    ("ASIA-PACIFIC", "India considers rice export duties", "Reuters"),
    ("EUROPE", "Euro zone PMI 51.7 in November", "Reuters"),
    ("ASIA-PACIFIC", "Nepal PM Shah ends his Delhi visit", "IANS"),
    ("EUROPE", "Thousands march in Lisbon on living costs", "JagranJosh"),
    ("EUROPE", "UK\u2013EU reset deal called \u201clandmark\u201d", "BBC"),
    ("ASIA-PACIFIC", "India\u2013EU pact likely signed 16 Dec", "JagranJosh"),
    ("ASIA-PACIFIC", "Tata Steel sells pipe unit, \u20b928,000 cr", "ObserverVoice"),
    ("ASIA-PACIFIC", "SpiceJet pilot seeks safety audit", "ObserverVoice"),
    ("ASIA-PACIFIC", "IFFI 2026 hosts BRICS Roundtable", "ObserverVoice"),
    ("ASIA-PACIFIC", "Modi opens AI Centre at IIT Patna", "ObserverVoice"),
    ("ASIA-PACIFIC", "JEE Main 2027 registration closes today", "JagranJosh"),
    ("ASIA-PACIFIC", "Google puts $5m into IIT Kharagpur AI", "JagranJosh"),
    ("AMERICAS", "US stocks fall; Nasdaq futures +3% Mon", "AP"),
    ("AMERICAS", "Goldman: +18% S&P 500 through 2027", "ActiveInvestorMag"),
    ("ASIA-PACIFIC", "KOSPI falls ~3% to a 10-month low", "Reuters"),
    ("AMERICAS", "Mets, A.J. Ewing agree $95m, 8 years", "AP"),
]

TIMELINE = [
    ("MON 12:52 UTC", "Bitcoin at $61,284", "CoinPaprika"),
    ("MON 13:39 UTC", "Hong Kong curbs for Interpol summit announced", "HK News TV"),
    ("MON EVENING", "Zelenskyy announces the Merkury sinking", "CNN / AP"),
    ("MON EVENING", "Treasury announces ~30 Iran sanctions", "Treasury"),
    ("MON EVENING", "COP31 falls; COP32 set for Addis Ababa 2027", "Reuters"),
    ("04:24 WIB TUE", "KCNA: N. Korea weighs closing Swiss office", "Reuters"),
]

DATECHECK = [
    ("186-drone night, 161 downed", "Fri 21\u2013Sun 22 Nov"),
    ("HK Election Committee results", "Sun 22 Nov"),
    ("Alcaraz wins ATP Finals", "Sun 22 Nov"),
    ("Verstappen wins Las Vegas GP", "Sun 22 Nov"),
    ("Wembanyama scores 50", "Sun 22 Nov"),
    ("Huang resigns as Nvidia CEO", "Thu 12 Nov"),
    ("Kerch Bridge strike reported", "Sun 22 Nov"),
]

NUMBERS = [
    ("7", "SEA DRONES LAUNCHED"),
    ("15", "KILLED NEAR KYIV"),
    ("NO DEAL", "FIRST SINCE 2000"),
    ("\u223c30", "IRAN HOUSES SANCTIONED"),
    ("$3,588", "GOLD \u00b7 +1.5%"),
    ("$61,284", "BITCOIN"),
    ("+31%", "NVIDIA \u00b7 HUANG BACK"),
]

# Simplified continent outlines (lon, lat) - schematic, drawn in code.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 71), (-110, 68), (-95, 69), (-85, 66), (-80, 62),
     (-65, 60), (-55, 52), (-60, 46), (-70, 42), (-75, 35), (-80, 32), (-84, 30),
     (-90, 29), (-97, 26), (-105, 22), (-110, 23), (-115, 29), (-122, 37), (-125, 42),
     (-124, 48), (-130, 55), (-145, 60), (-158, 58), (-168, 66)],
    [(-80, 9), (-75, 11), (-65, 10), (-55, 6), (-50, 0), (-45, -5), (-38, -8),
     (-35, -10), (-40, -20), (-48, -28), (-55, -35), (-65, -40), (-70, -50), (-73, -53),
     (-72, -40), (-70, -30), (-78, -18), (-81, -10), (-80, -3), (-80, 9)],
    [(-18, 35), (-10, 37), (-5, 35), (0, 36), (10, 37), (20, 40), (30, 36),
     (36, 36), (35, 31), (43, 12), (48, 11), (51, 10), (45, -1), (40, -10),
     (36, -18), (32, -28), (26, -34), (19, -35), (15, -27), (12, -18), (9, -1),
     (9, 4), (-8, 5), (-15, 12), (-17, 21), (-18, 35)],
    [(10, 70), (20, 70), (30, 71), (40, 68), (50, 68), (60, 69), (70, 72),
     (80, 73), (100, 76), (120, 73), (140, 72), (160, 70), (178, 66), (170, 60),
     (160, 55), (142, 50), (140, 40), (130, 35), (122, 30), (115, 23), (108, 18),
     (105, 9), (100, 6), (95, 10), (90, 15), (85, 20), (80, 15), (75, 10),
     (70, 8), (60, 25), (55, 27), (50, 29), (45, 29), (40, 30), (35, 31),
     (30, 36), (25, 40), (20, 44), (15, 44), (10, 45), (5, 43), (0, 40),
     (-5, 36), (-10, 37), (-5, 42), (0, 48), (5, 53), (8, 57), (10, 62), (10, 70)],
    [(113, -22), (122, -14), (130, -12), (137, -12), (142, -11), (146, -19),
     (150, -22), (153, -27), (150, -37), (145, -38), (140, -38), (135, -35),
     (130, -32), (125, -33), (118, -35), (113, -22)],
]
# (lon, lat) pins per card number (slightly spread in the Europe cluster for legibility)
PINS = {1: (33.0, 52.0), 2: (21.0, 62.0), 3: (-77.0, 38.9), 4: (17.0, 33.0),
        5: (34.0, 38.0), 6: (37.0, 31.0), 7: (47.0, 16.0), 8: (-74.0, 40.7),
        9: (-3.0, 53.5), 10: (103.8, 1.4), 11: (-118.2, 34.0), 12: (-6.0, 55.0),
        13: (-77.0, 35.0), 14: (174.8, -41.3)}


# ---------------------------------------------------------------- rendering
def region_counts():
    counts = {}
    for c in CARDS:
        counts[c[1]] = counts.get(c[1], 0) + 1
    for b in BRIEFS:
        counts[b[0]] = counts.get(b[0], 0) + 1
    return counts


def draw_card(draw, box, card, lead, variant):
    num, region, place, head, deck, chip, src, first, kind, sky, ground, accent = card
    x0, y0, x1, y1 = box
    cw = x1 - x0
    draw.rectangle(box, fill=WHITE, outline=TEAL_D, width=3)
    col = REGION_COLORS[region]
    bs = 84 if lead else 68
    # number badge, top-left; region + place to its right
    draw.rectangle([x0, y0, x0 + bs, y0 + bs], fill=col)
    draw.text((x0 + bs // 2, y0 + bs // 2), str(num),
              font=font(F_SANS_B, 52 if lead else 42), fill=WHITE, anchor="mm")
    rf = font(F_SANS_B, 32 if lead else 26)
    rt = "%s \u00b7 %s" % (region, place)
    while draw.textlength(rt, font=rf) > cw - bs - 24 and rf.size > 20:
        rf = font(F_SANS_B, rf.size - 2)
    draw.text((x0 + bs + 14, y0 + bs // 2), rt, font=rf, fill=col, anchor="lm")
    ty = y0 + bs + 12
    f_head = font(F_SANS_B, 58 if lead else 42)
    ty = draw_wrapped(draw, x0 + 16, ty, head, f_head, cw - 32, INK,
                      leading=int(f_head.size * 1.14), max_lines=3 if lead else 2)
    ty += 8
    f_deck = font(F_SANS, 44 if lead else 34)
    ty = draw_wrapped(draw, x0 + 16, ty, deck, f_deck, cw - 32, (40, 50, 48),
                      leading=int(f_deck.size * 1.22), max_lines=2)
    # scene strip at the bottom, above the source tag
    tag_h = 40 if lead else 34
    sh = (y1 - tag_h - 8) - ty
    sh = max(70, sh)
    sy0 = y1 - tag_h - 8 - sh
    scene(draw, (x0 + 3, sy0, x1 - 3, y1 - tag_h - 8), kind, sky, ground, accent)
    # chip over the strip bottom (auto-fit so it never overflows the card)
    csize = 34 if lead else 30
    while csize > 20 and draw.textlength(chip, font=font(F_SANS_B, csize)) + 26 > cw - 28:
        csize -= 2
    cf = font(F_SANS_B, csize)
    cy = y1 - tag_h - 8 - 42
    draw.rectangle([x0 + 14, cy, x0 + 14 + draw.textlength(chip, font=cf) + 26, cy + 40],
                   fill=BLACK)
    draw.text((x0 + 27, cy + 20), chip, font=cf, fill=(255, 214, 90), anchor="lm")
    # source tag pinned at the bottom (single primary source on minis)
    tag_src = src if lead else src.split(" / ")[0]
    tag = "REPORTED \u00b7 %s \u00b7 %s" % (tag_src, first)
    tf = font(F_SANS_B, 30 if lead else 24)
    while draw.textlength(tag, font=tf) > cw - 32 and tf.size > 18:
        tf = font(F_SANS_B, tf.size - 2)
    draw.text((x0 + 16, y1 - 8), tag, font=tf, fill=GREY, anchor="lb")


def draw_map(draw, box):
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=(232, 240, 238), outline=TEAL_D, width=3)
    mw, mh = x1 - x0, y1 - y0

    def px(lon, lat):
        return (x0 + (lon + 180.0) / 360.0 * mw,
                y0 + (90.0 - lat) / 180.0 * mh)

    for poly in CONTINENTS:
        pts = [px(lon, lat) for lon, lat in poly]
        minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
        miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)
        step = 13
        for gx in range(int(minx), int(maxx), step):
            for gy in range(int(miny), int(maxy), step):
                inside = False
                j = len(pts) - 1
                for i in range(len(pts)):
                    xi, yi = pts[i]; xj, yj = pts[j]
                    if ((yi > gy) != (yj > gy)) and (gx < (xj - xi) * (gy - yi) / (yj - yi) + xi):
                        inside = not inside
                    j = i
                if inside:
                    draw.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=TEAL_D)
    for num, (lon, lat) in sorted(PINS.items()):
        cx, cy = px(lon, lat)
        draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=RED, outline=WHITE, width=3)
        draw.text((cx, cy), str(num), font=font(F_SANS_B, 19), fill=WHITE, anchor="mm")


def render(variant, out_path):
    img = Image.new("RGB", (W, W), PAPER)
    d = ImageDraw.Draw(img)
    counts = region_counts()
    total = len(CARDS) + len(BRIEFS)
    assert total == 36, total
    assert sum(counts.values()) == 36
    assert len(counts) == 7, counts

    y = 48
    # kicker
    kick = "%d STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE FROM TUESDAY 24 NOVEMBER 2026" % total
    d.text((W // 2, y + 22), kick, font=font(F_SANS_B, 46), fill=TEAL_D, anchor="mm")
    d.line([M, y + 58, W - M, y + 58], fill=TEAL_D, width=5)
    y += 78
    # masthead
    if variant == "B":
        d.rectangle([M, y, W - M, y + 200], fill=TEAL_D)
        d.text((W // 2, y + 100), "THE HARBOUR LIGHT", font=font(F_SERIF_B, 170),
               fill=WHITE, anchor="mm")
        d.line([M, y + 200, W - M, y + 200], fill=GOLD, width=8)
        y += 216
    else:
        d.text((W // 2, y + 88), "THE HARBOUR LIGHT", font=font(F_SERIF_B, 180),
               fill=TEAL_D, anchor="mm")
        d.line([M, y + 182, W - M, y + 182], fill=GOLD, width=6)
        y += 196
    # date line
    d.text((W // 2, y + 56), "Tuesday 24 November 2026", font=font(F_SERIF_B, 108),
           fill=INK, anchor="mm")
    y += 122
    # lead deck
    deck = ("Seven sea drones sink the Merkury off Libya. Kyiv counts at least 15 dead. "
            "Washington sanctions some thirty Iran exchange houses.")
    f_deck = font(F_SERIF_I, 56)
    y = draw_wrapped(d, M, y, deck, f_deck, CW, TEAL_D, leading=62)
    y += 14
    # number strip
    nw = CW // 7
    for i, (big, label) in enumerate(NUMBERS):
        x = M + i * nw
        d.rectangle([x + 4, y, x + nw - 4, y + 128], fill=TEAL_L, outline=TEAL_D, width=3)
        d.text((x + nw // 2, y + 40), big, font=font(F_SANS_B, 52), fill=TEAL_D, anchor="mm")
        for j, ln in enumerate(wrap(d, label, font(F_SANS_B, 26), nw - 24)):
            d.text((x + nw // 2, y + 84 + j * 28), ln, font=font(F_SANS_B, 26),
                   fill=INK, anchor="mm")
    y += 148
    # region strip
    order = ["EUROPE", "MIDDLE EAST", "AMERICAS", "ASIA-PACIFIC", "WORLD", "OCEANIA", "AFRICA"]
    x = M
    for reg in order:
        label = "%s %d" % (reg, counts[reg])
        wdt = d.textlength(label, font=font(F_SANS_B, 34)) + 44
        d.rectangle([x, y, x + wdt, y + 62], fill=REGION_COLORS[reg])
        d.text((x + wdt // 2, y + 31), label, font=font(F_SANS_B, 34), fill=WHITE, anchor="mm")
        x += wdt + 12
    y += 84
    # lead row: 3 lead cards (variant B swaps leads 2 and 3)
    leads = CARDS[:3] if variant == "A" else [CARDS[0], CARDS[2], CARDS[1]]
    lw = (CW - 2 * 36) // 3
    lead_h = 560
    for i in range(3):
        draw_card(d, (M + i * (lw + 36), y, M + i * (lw + 36) + lw, y + lead_h),
                  leads[i], True, variant)
    y += lead_h + 22
    # mini grid: remaining 11 cards, 6 columns x 2 rows
    minis = CARDS[3:]
    cols = 6
    mw2 = (CW - (cols - 1) * 22) // cols
    mh2 = 380
    rows = (len(minis) + cols - 1) // cols
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(minis):
                break
            xx = M + c * (mw2 + 22)
            draw_card(d, (xx, y, xx + mw2, y + mh2), minis[idx], False, variant)
        y += mh2 + 20
    y -= 20
    y += 22
    # timeline strip (full width)
    d.text((M, y), "THE DAY IN TIME \u2014 REPORTED MON 23 NOV EVENING \u2192 TUE 24 NOV 04:24 WIB",
           font=font(F_SANS_B, 34), fill=TEAL_D)
    y += 48
    tw = CW // 6
    for i, (tm, ev, src) in enumerate(TIMELINE):
        x = M + i * tw
        d.rectangle([x + 3, y, x + tw - 3, y + 100], fill=WHITE, outline=TEAL, width=2)
        d.text((x + 14, y + 9), tm, font=font(F_SANS_B, 26), fill=RED)
        draw_wrapped(d, x + 14, y + 40, ev, font(F_SANS, 26), tw - 28, INK,
                     leading=30, max_lines=2)
    y += 100 + 18
    # bottom: map + date check (left) | ALSO ON (right)
    left_w = 1240
    right_x = M + left_w + 36
    right_w = W - M - right_x
    by = y
    d.text((M, by), "WHERE IT HAPPENED \u2014 pins match story numbers",
           font=font(F_SANS_B, 36), fill=TEAL_D)
    draw_map(d, (M, by + 48, M + left_w, by + 48 + 230))
    dy = by + 48 + 230 + 12
    dch = 210
    d.rectangle([M, dy, M + left_w, dy + dch], fill=RED_L, outline=RED, width=4)
    d.text((M + 16, dy + 12), "DATE CHECK \u2014 NOT TODAY\u2019S NEWS", font=font(F_SANS_B, 32), fill=RED)
    yy = dy + 54
    half = (len(DATECHECK) + 1) // 2
    for col_i, group in enumerate((DATECHECK[:half], DATECHECK[half:])):
        xx = M + 16 + col_i * (left_w // 2)
        y2 = yy
        for name, when in group:
            d.text((xx, y2), "\u2022 %s \u2014 %s" % (name, when), font=font(F_SANS, 25), fill=INK)
            y2 += 34
    # ALSO ON right column: 2 sub-columns, one line per brief (auto-shrink)
    d.text((right_x, by), "ALSO ON \u2014 TUESDAY 24 NOVEMBER 2026",
           font=font(F_SANS_B, 36), fill=TEAL_D)
    subcols = 2
    sw = right_w // subcols
    per = (len(BRIEFS) + subcols - 1) // subcols
    for ci in range(subcols):
        group = BRIEFS[ci * per:(ci + 1) * per]
        xx = right_x + ci * sw
        y2 = by + 52
        for j, (reg, text, src) in enumerate(group):
            n = 15 + ci * per + j
            d.text((xx, y2), "%d." % n, font=font(F_SANS_B, 28), fill=REGION_COLORS[reg])
            bf = font(F_SANS, 28)
            while bf.size > 22 and d.textlength(text, font=bf) > sw - 70:
                bf = font(F_SANS, bf.size - 2)
            d.text((xx + 58, y2), text, font=bf, fill=INK)
            y2 += 40
    # footer
    fy = by + 48 + 230 + 12 + dch + 12
    d.line([M, fy, W - M, fy], fill=TEAL_D, width=4)
    foot = ("Sources: Reuters \u00b7 AP \u00b7 BBC \u00b7 CNN \u00b7 Times \u00b7 WSJ \u00b7 Guardian \u00b7 "
            "Treasury \u00b7 CoinPaprika \u00b7 IANS \u00b7 JagranJosh \u00b7 ObserverVoice. "
            "REPORTED = reported by the named source; CLAIM = as claimed, not confirmed. "
            "Pictures and map: original, drawn in code. THE HARBOUR LIGHT \u2014 Tuesday 24 November 2026.")
    draw_wrapped(d, M, fy + 14, foot, font(F_SANS, 28), CW, GREY, leading=36, max_lines=2)
    print("footer rule y:", fy, "of", W)
    img.save("/tmp/harbour-%s-3000.png" % variant)
    small = img.resize((1024, 1024), Image.LANCZOS)
    # keep the palette PNG: ~230 KB, inside the 190-450 KB target (RGB re-save was ~640 KB)
    small = small.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    small.save(out_path, optimize=True)
    print("wrote", out_path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="A")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(a.variant, a.out)
