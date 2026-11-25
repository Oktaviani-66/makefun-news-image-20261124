#!/usr/bin/env python3
"""THE LANTERN GAZETTE - front page for Tuesday 24 November 2026.
Build-time renderer (Pillow, local only). Draws entry.png 1024x1024.
Palette: black ink + burnt orange on ivory. Layout B: one full-width
lead, two half leads, ten mini cards, ALSO ON left + dotted map right.
All facts from the locked NI24 pool (ni24-pool.md + 07:00 refresh).
Variant A: Merkury full-width lead. Variant B: Huang full-width lead,
Merkury demoted to half lead, grid order rotated, strips swapped.
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

FD = "/home/hatch/workspace/tools/bedah-19nov/news-image/fonts"
def F(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)
PB = lambda s: F("PlayfairDisplay-Black.ttf", s)
PBo = lambda s: F("PlayfairDisplay-Bold.ttf", s)
PI = lambda s: F("PlayfairDisplay-Italic.ttf", s)
AB = lambda s: F("Archivo-Bold.ttf", s)
AR = lambda s: F("Archivo.ttf", s)

IVORY = (246, 240, 226); PAPER = (250, 246, 236); INK = (22, 20, 18)
ORANGE = (198, 84, 16); ORANGE_D = (156, 62, 8); TAN = (232, 220, 196)
GREY = (96, 90, 82); LINE = (60, 54, 46); RED = (164, 32, 24)
NAVY = (26, 42, 74); WHITE = (255, 255, 255)
REG_COL = {"EUROPE": (44, 92, 160), "MIDDLE EAST": (178, 108, 20),
           "AFRICA": (122, 74, 160), "AMERICAS": (178, 44, 36),
           "ASIA": (30, 128, 110), "SOUTH ASIA": (200, 130, 30),
           "ASIA-PACIFIC": (70, 130, 60), "OCEANIA": (30, 110, 170),
           "WORLD": (90, 90, 90)}

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

# ---------------- flat layered scene painters ----------------
def sea(d, x, y, w, h, sky=(70, 96, 130)):
    d.rectangle([x, y, x + w, y + h], fill=sky)
    d.rectangle([x, y + int(h * .62), x + w, y + h], fill=(38, 74, 110))
    for i in range(5):
        yy = y + int(h * .68) + i * max(3, int(h * .07))
        d.line([x + 4, yy, x + w - 4, yy], fill=(90, 140, 180), width=1)

def scene_ship_sink(d, x, y, w, h):
    sea(d, x, y, w, h, sky=(96, 84, 70))
    cx, cy = x + w // 2, y + int(h * .58)
    d.polygon([(cx - w//4, cy), (cx + w//4, cy - 6), (cx + w//5, cy + 14), (cx - w//5, cy + 12)], fill=(52, 54, 58))
    d.rectangle([cx - 30, cy - 26, cx + 8, cy - 2], fill=(70, 72, 76))
    d.rectangle([cx + 12, cy - 18, cx + 30, cy - 2], fill=(70, 72, 76))
    d.line([cx - 4, cy - 40, cx - 4, cy - 4], fill=(30, 30, 30), width=3)
    for i in range(3):  # sea drones arcing in
        sx = x + 16 + i * 26; sy = y + 10 + i * 7
        d.polygon([(sx, sy), (sx + 18, sy + 3), (sx + 4, sy + 8)], fill=INK)
    d.ellipse([cx + w//5, cy - 30, cx + w//5 + 26, cy - 4], fill=ORANGE)  # fire
    d.ellipse([cx + w//5 + 6, cy - 24, cx + w//5 + 20, cy - 10], fill=(240, 180, 60))

def scene_chart_up(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 34, 44))
    for i in range(4):
        yy = y + 8 + i * (h - 16) // 3
        d.line([x + 4, yy, x + w - 4, yy], fill=(70, 80, 96), width=1)
    pts = [(x + 8, y + h - 12), (x + w//3, y + h - 20), (x + w//2, y + h - 34), (x + w - 10, y + 10)]
    d.line(pts, fill=(70, 220, 110), width=4)
    d.polygon([(x + w - 22, y + 16), (x + w - 8, y + 8), (x + w - 10, y + 24)], fill=(70, 220, 110))
    d.text((x + 8, y + 6), "+31%", font=AB(17), fill=(70, 220, 110))

def scene_climate(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(104, 128, 148))
    d.rectangle([x, y + int(h * .7), x + w, y + h], fill=(70, 84, 66))
    for i, bx in enumerate(range(x + 8, x + w - 30, max(26, w // 5))):
        d.rectangle([bx, y + 16, bx + 20, y + int(h * .7)], fill=(210, 204, 190))
        d.polygon([(bx - 2, y + 16), (bx + 10, y + 6), (bx + 22, y + 16)], fill=ORANGE_D)
    d.ellipse([x + w - 44, y + 8, x + w - 12, y + 40], outline=WHITE, width=3)
    d.line([x + w - 40, y + 12, x + w - 16, y + 36], fill=RED, width=4)

def scene_generic(d, kind, x, y, w, h):
    skies = {"war": (110, 96, 84), "city": (96, 110, 128), "money": (52, 66, 52),
             "sport": (70, 120, 70), "sea2": (70, 96, 130), "tech": (44, 48, 70),
             "vote": (90, 84, 110), "coin": (80, 70, 40), "game": (60, 44, 84),
             "desert": (168, 138, 92)}
    d.rectangle([x, y, x + w, y + h], fill=skies.get(kind, (100, 100, 100)))
    gy = y + int(h * .72)
    d.rectangle([x, gy, x + w, y + h], fill=(58, 54, 48))
    if kind == "war":
        for bx in range(x + 6, x + w - 20, 30):
            hh = 14 + (bx * 7) % 16
            d.rectangle([bx, gy - hh, bx + 18, gy], fill=(84, 78, 70))
        d.ellipse([x + w - 34, y + 6, x + w - 14, y + 26], fill=ORANGE)
    elif kind == "city":
        for bx in range(x + 4, x + w - 16, 22):
            hh = 18 + (bx * 5) % 20
            d.rectangle([bx, gy - hh, bx + 14, gy], fill=(150, 156, 166))
            d.rectangle([bx + 3, gy - hh + 4, bx + 7, gy - hh + 8], fill=(250, 220, 120))
    elif kind in ("money", "coin"):
        for i, bx in enumerate(range(x + 10, x + w - 14, 20)):
            bh = 8 + i * 5
            d.rectangle([bx, gy - bh, bx + 12, gy], fill=(216, 178, 60) if kind == "coin" else (110, 180, 110))
        d.text((x + 6, y + 4), "$", font=AB(16), fill=(250, 230, 150))
    elif kind == "sport":
        d.ellipse([x + w//2 - 10, gy - 22, x + w//2 + 10, gy - 2], fill=WHITE, outline=INK)
        d.line([x + 6, gy - 4, x + w - 6, gy - 4], fill=WHITE, width=2)
    elif kind == "sea2":
        d.rectangle([x, gy, x + w, y + h], fill=(38, 74, 110))
        d.polygon([(x + w//3, gy - 4), (x + 2*w//3, gy - 4), (x + w//2 + 8, gy + 8), (x + w//2 - 8, gy + 8)], fill=(200, 200, 205))
        d.rectangle([x + w//2 - 4, gy - 20, x + w//2 + 10, gy - 4], fill=(160, 60, 40))
        d.ellipse([x + w - 30, y + 4, x + w - 14, y + 20], fill=ORANGE)
    elif kind == "tech":
        for i in range(3):
            d.rectangle([x + 8 + i * 22, y + 8, x + 24 + i * 22, gy - 4], outline=(120, 200, 230), width=2)
        d.ellipse([x + w - 26, y + 8, x + w - 10, y + 24], fill=(120, 200, 230))
    elif kind == "vote":
        d.rectangle([x + 10, gy - 30, x + w - 10, gy], fill=(226, 220, 205))
        for cxx in range(x + 16, x + w - 14, 16):
            d.line([cxx, gy - 28, cxx, gy - 2], fill=(120, 114, 100), width=3)
        d.polygon([(x + 6, gy - 30), (x + w//2, gy - 40), (x + w - 6, gy - 30)], fill=ORANGE_D)
    elif kind == "game":
        d.rectangle([x + 12, gy - 26, x + 44, gy - 6], fill=(30, 30, 36))
        d.rectangle([x + 16, gy - 22, x + 40, gy - 10], fill=(90, 200, 160))
        d.text((x + 50, y + 8), "$3.8bn", font=AB(13), fill=(250, 220, 120))
    elif kind == "desert":
        d.ellipse([x + 8, y + 6, x + 34, y + 32], fill=(240, 200, 90))
        d.polygon([(x + 10, gy), (x + w//2, gy - 22), (x + w - 12, gy)], fill=(150, 116, 70))

SCENES = {"ship": scene_ship_sink, "chart": scene_chart_up, "climate": scene_climate}

def draw_scene(img, kind, x, y, w, h):
    # render on a sub-image so scene art can never spill outside its strip
    sub = Image.new("RGB", (w, h), IVORY)
    sd = ImageDraw.Draw(sub)
    if kind in SCENES:
        SCENES[kind](sd, 0, 0, w, h)
    else:
        scene_generic(sd, kind, 0, 0, w, h)
    img.paste(sub, (x, y))

# ---------------- card data (pool-locked) ----------------
# num, region, place, kind, headline, deck, chip, source
CARDS = {
 1: (1, "EUROPE", "BENGHAZI, LIBYA - WAR", "ship",
     "Ukraine sinks Russian warship Merkury off Libya",
     "7 sea drones launched; Steregushchiy-class corvette sunk at Benghazi. Ka-27 helicopter destroyed aboard; cargo ship MV Angara also hit. SBU: both were legitimate military targets on the 'Syrian Express' supply line; satellite photos show the corvette sunk at her berth.",
     "7 SEA DRONES - MERKURY SUNK", "CNN/AP - REPORTED"),
 20: (20, "AMERICAS", "NEW YORK - MARKETS", "chart",
     "Nvidia brings back Jensen Huang as CEO; shares +31%",
     "Board reinstates Huang Mon after Trump intervened; he quit 12 Nov. Nasdaq +6%, S&P 500 +5%, chip index +12% in one day.",
     "+31% - HUANG BACK", "REUTERS - REPORTED"),
 4: (4, "WORLD", "ANTALYA, TURKIYE - CLIMATE", "climate",
     "COP31 ends with NO DEAL - first since 2000",
     "The Antalya Pact was NOT adopted: final text dropped every mention of fossil fuels after 44 h overtime, the longest COP ever. 130 states wanted the language; >90 signed a side pledge.",
     "NO DEAL - 44H OVERTIME", "REUTERS/GUARDIAN - REPORTED"),
 3: (3, "EUROPE", "KYIV REGION, UKRAINE - WAR", "war",
     "Russian strikes kill at least 15 near Kyiv",
     "Kyiv strikes: 11 killed in a block of flats in Dymer; a drone hit a 6-floor Kyiv building Mon, 5 injured. Zelenskyy on Putin: 'a killer'.",
     "15 KILLED - 11 IN DYMER", "TIMES/AP - REPORTED"),
 2: (2, "EUROPE", "GULF OF FINLAND - SEA", "sea2",
     "Russian cargo ship Sparta II hit, towed clear",
     "121 m ship hit by 2 drones; Finland led the Loviisa rescue, all 16 crew off safe, towed out Sunday night.",
     "121M - 16 CREW SAFE", "REUTERS - REPORTED"),
 5: (5, "MIDDLE EAST", "WASHINGTON - SANCTIONS", "vote",
     "Iran sanctions: US targets ~30 exchange houses",
     "Treasury Mon targets ~30 exchange houses and executives, the core of shadow banking evading sanctions on Iranian banks.",
     "~30 SANCTIONED", "AP/TREASURY - REPORTED"),
 6: (6, "MIDDLE EAST", "GAZA CITY - CONFLICT", "city",
     "Israeli strikes kill 3 in Gaza",
     "3 killed Mon in separate strikes, including a UNRWA employee; Shifa Hospital and the agency confirm the toll.",
     "3 KILLED", "AP - REPORTED"),
 7: (7, "MIDDLE EAST", "WESTERN YEMEN - WAR", "desert",
     "Strike kills 11 in western Yemen",
     "Houthis say a Saudi-backed forces' strike Mon killed 11 people and wounded 19 in western Yemen.",
     "11 KILLED - 19 WOUNDED", "AP - REPORTED"),
 8: (8, "AMERICAS", "MARKETS - GOLD", "coin",
     "Gold rebounds 1.5% to $3,588 an ounce",
     "Bullion +1.5% Mon after its worst week in 8 months - gold 3588 in dollar terms at Monday's print; traders await the US PCE report due 25 Nov. 10-yr yield ~4.96%.",
     "$3,588/OZ +1.5%", "REUTERS - REPORTED"),
 9: (9, "WORLD", "CRYPTO - BITCOIN", "coin",
     "Bitcoin steadies near $61,284",
     "$61,284 Mon 12:52 UTC (bitcoin 61284 on the tape), +1.1% in 24 h, -4.5% in 7 days; weekend low near $55,100. Kraken CAD flash crash Sat; trades stand.",
     "$61,284", "COINPAPRIKA - REPORTED"),
 10: (10, "AMERICAS", "LOS ANGELES - BUSINESS", "game",
     "GTA VI takes $3.8bn on day one",
     "$3.8bn first day - the biggest entertainment launch on record, past every game launch and single-day film box office.",
     "$3.8BN DAY ONE", "ACTIVEINVESTOR - REPORTED"),
 14: (14, "AMERICAS", "WASHINGTON - POLITICS", "vote",
     "Democrats take both chambers, 258-173",
     "Largest House majority since 1992: Democrats 258 seats to 173 after the North Carolina pickup; Van Hollen challenges Schumer, ballot 1 Dec.",
     "258-173 HOUSE", "BBC - REPORTED"),
 11: (11, "OCEANIA", "WELLINGTON - CRICKET", "sport",
     "New Zealand bat out a draw with India",
     "NZ 239/5: Mitchell 49* off 186 balls, Phillips 26*; India 720/9 declared (Rahul 136, Pant 128). 2nd Test 27 Nov.",
     "DRAWN - 239/5", "HS - REPORTED"),
}
BRIEFS = [
 (15, "FBI probes hack of its crime database; Washington State pauses dealer checks (AP)"),
 (16, "Solana launches solana.ai for autonomous AI agents (Gadgets360)"),
 (17, "UN AI weapons talks to continue: states agree to keep negotiating (salonvision)"),
 (18, "Miley Cyrus marries Maxx Morando in California (Reuters)"),
 (19, "Hong Kong curbs drones for Interpol summit 30 Nov-3 Dec (HK News TV)"),
 (21, "North Korea weighs shutting Swiss office in Pyongyang (KCNA/Reuters)"),
 (22, "US discussing military training for Syrian forces, demining focus (Reuters)"),
 (23, "Congo halts cobalt exports from 30 Nov over oversupply (Reuters)"),
 (24, "Indonesia: 24 killed in factory blaze, dozens missing (Reuters)"),
 (25, "CrowdStrike snaps up Zscaler in $44bn cyber deal (Reuters)"),
 (26, "Nepal PM Shah ends Delhi state visit, met Modi Monday (IANS)"),
 (27, "Thousands march in Lisbon over cost of living (JagranJosh)"),
 (28, "UK-EU Brexit reset: Burnham calls deal 'landmark' (BBC)"),
 (29, "India-EU trade pact likely signed 16 Dec in Brussels (JagranJosh)"),
 (30, "Tata Steel sells pipe arm to APL Apollo, Rs28,000 crore (ObserverVoice)"),
 (31, "KOSPI falls ~3% Monday to a 10-month low (Reuters)"),
 (32, "Mets and A.J. Ewing agree $95m, 8-year deal (AP)"),
 (33, "India considers rice export duties as prices rise (Reuters)"),
 (34, "Euro zone PMI 51.7 in November, fifth month of growth (Reuters)"),
 (35, "US Army to detonate lead stockpile in Iowa, ~10,000 lb (Reuters)"),
 (36, "Trump hosts gala for meme-coin investors (Reuters)"),
 (37, "FORECAST: US PCE inflation report due 25 Nov (pool)"),
 (38, "Liverpool 4-0 Man Utd; Yoro off 8th min, United 19th; Pochettino debut disaster (Mint)"),
]
REGIONS_OF = {1:"EUROPE",20:"AMERICAS",4:"WORLD",3:"EUROPE",2:"EUROPE",5:"MIDDLE EAST",
 6:"MIDDLE EAST",7:"MIDDLE EAST",8:"AMERICAS",9:"WORLD",10:"AMERICAS",14:"AMERICAS",
 11:"OCEANIA",15:"AMERICAS",16:"WORLD",17:"WORLD",18:"AMERICAS",19:"ASIA-PACIFIC",
 21:"ASIA",22:"MIDDLE EAST",23:"AFRICA",24:"ASIA-PACIFIC",25:"AMERICAS",26:"SOUTH ASIA",
 27:"EUROPE",28:"EUROPE",29:"SOUTH ASIA",30:"SOUTH ASIA",31:"ASIA-PACIFIC",32:"AMERICAS",
 33:"SOUTH ASIA",34:"EUROPE",35:"AMERICAS",36:"AMERICAS",37:"AMERICAS",38:"EUROPE"}
TOTAL = len(CARDS) + len(BRIEFS)  # 36
NREG = len(set(REGIONS_OF.values()))  # 9

# ---------------- drawing ----------------
def card(img, key, x, y, w, h, lead=False):
    d = ImageDraw.Draw(img)
    num, reg, place, kind, head, deck, chip, src = CARDS[key]
    d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=INK, width=2)
    sh = 44 if lead else 30
    draw_scene(img, kind, x + 2, y + 2, w - 4, sh)
    d.rectangle([x + 4, y + sh - 13, x + 4 + d.textlength(chip, font=AB(9)) + 8, y + sh + 1], fill=ORANGE)
    d.text((x + 8, y + sh - 11), chip, font=AB(9), fill=WHITE)
    yy = y + sh + 4
    d.text((x + 5, yy), "%d. %s" % (num, place), font=AB(8 if not lead else 9), fill=REG_COL[reg])
    yy += 12 if not lead else 14
    hf = AB(13) if lead else AB(10)
    for ln in wrap(d, head, hf, w - 10)[:3]:
        d.text((x + 5, yy), ln, font=hf, fill=INK); yy += (16 if lead else 12)
    df = AR(9) if lead else AR(8)
    for ln in wrap(d, deck, df, w - 10)[:4 if lead else 3]:
        d.text((x + 5, yy), ln, font=df, fill=(52, 48, 44)); yy += 11
    d.text((x + 5, y + h - 11), src, font=AB(7), fill=GREY)

# dotted world map: coarse land dots from a tiny grid map
LAND = [
"..........####..........####................................",
"......#########......##########......##..####.................",
".....##########.....############....################..........",
"......########.......##########....##################.........",
".......######.........########......################..........",
"........####..........######.........##############...........",
".........##............####...........############............",
"........................##.............########..............",
"........................................######................",
".........................................####.................",
]
PINS = [(1, 30, 3), (3, 34, 2), (4, 33, 4), (20, 8, 3), (8, 10, 4), (11, 55, 7), (6, 36, 4), (23, 31, 6)]

def draw_map(img, x, y, w, h):
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w, y + h], fill=NAVY, outline=INK, width=2)
    d.text((x + 6, y + 4), "WHERE IT HAPPENED", font=AB(10), fill=WHITE)
    cw = (w - 12) / 62.0; chh = (h - 44) / 10.0
    for r, row in enumerate(LAND):
        for c, ch in enumerate(row[:62]):
            if ch == "#":
                cx = x + 6 + c * cw; cy = y + 20 + r * chh
                d.ellipse([cx, cy, cx + 2.4, cy + 2.4], fill=(170, 190, 220))
    for num, gx, gy in PINS:
        cx = x + 6 + gx * cw; cy = y + 20 + gy * chh
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=ORANGE, outline=WHITE)
        t = str(num); tw = d.textlength(t, font=AB(8))
        d.text((cx - tw / 2, cy - 5), t, font=AB(8), fill=WHITE)
    d.text((x + 6, y + h - 13), "Pins match story numbers.", font=AR(8), fill=(200, 210, 230))

def header(d, variant):
    d.rectangle([0, 0, 1024, 1024], fill=IVORY)
    d.rectangle([0, 0, 1024, 30], fill=INK)
    d.text((14, 8), "EST. TUESDAY - ONE DAY, ONE PAGE - ALL STORIES DATED", font=AB(11), fill=(240, 200, 150))
    r = "No. 24 - PRICE: THE DAY ITSELF"
    d.text((1010 - d.textlength(r, font=AB(11)), 8), r, font=AB(11), fill=(240, 200, 150))
    d.text((14, 38), "THE LANTERN GAZETTE", font=PB(58), fill=INK)
    d.rectangle([14, 104, 1010, 108], fill=ORANGE)
    d.text((14, 114), "Tuesday 24 November 2026", font=PB(40), fill=ORANGE_D)
    d.text((620, 128), "The whole day, lit on one page.", font=PI(17), fill=GREY)
    kick = "%d DATED STORIES - %d REGIONS - EVERY ONE TUESDAY 24 NOVEMBER 2026" % (TOTAL, NREG)
    d.rectangle([14, 162, 1010, 186], fill=ORANGE)
    d.text((24, 168), kick, font=AB(14), fill=WHITE)
    # numbers strip
    nums = [("7", "sea drones"), ("$3,588", "gold +1.5%"), ("$61,284", "Bitcoin"),
            ("+31%", "Nvidia/Huang"), ("258-173", "US House"), ("239/5", "Wellington draw"),
            ("NO DEAL", "COP31"), ("$3.8bn", "GTA VI day 1")]
    d.rectangle([14, 192, 1010, 232], outline=INK, width=2)
    cw = 996 / 8
    for i, (n, lab) in enumerate(nums):
        xx = 14 + i * cw
        if i: d.line([xx, 194, xx, 230], fill=LINE, width=1)
        tw = d.textlength(n, font=AB(17)); d.text((xx + (cw - tw) / 2, 196), n, font=AB(17), fill=ORANGE_D)
        tw = d.textlength(lab, font=AR(9)); d.text((xx + (cw - tw) / 2, 218), lab, font=AR(9), fill=INK)
    # region strip
    from collections import Counter
    cnt = Counter(REGIONS_OF.values())
    order = ["EUROPE", "MIDDLE EAST", "AFRICA", "AMERICAS", "ASIA", "SOUTH ASIA", "ASIA-PACIFIC", "OCEANIA", "WORLD"]
    xx = 14; yy = 238
    for reg in order:
        lab = "%s %d" % (reg, cnt[reg]); twd = d.textlength(lab, font=AB(10)) + 14
        d.rectangle([xx, yy, xx + twd, yy + 18], fill=REG_COL[reg])
        d.text((xx + 7, yy + 3), lab, font=AB(10), fill=WHITE); xx += twd + 5
    # timeline
    tl = [("04:24 WIB TUE", "KCNA: N. Korea weighs Swiss office closure"),
          ("MON EVE UTC", "Zelenskyy announces Merkury sinking"),
          ("MON EVE UTC", "Treasury sanctions ~30 Iran houses"),
          ("12:52 UTC MON", "Bitcoin prints $61,284"),
          ("21:39 HKT MON", "HK sets Interpol-summit curbs"),
          ("SUN NIGHT", "Sparta II towed clear; COP31 ends")]
    d.rectangle([14, 256, 1010, 284], fill=TAN, outline=LINE, width=1)
    d.text((20, 259), "THE DAY IN TIME", font=AB(9), fill=INK)
    xx = 20
    for t, ev in tl:
        s = "%s %s" % (t, ev)
        if xx + d.textlength(s, font=AR(8)) > 1000:
            break
        d.text((xx, 271), s + "  |", font=AR(8), fill=(60, 54, 46)); xx += d.textlength(s + "  |", font=AR(8)) + 4

def bottom(img, variant):
    d = ImageDraw.Draw(img)
    # ALSO ON left, map right (Layout B); variant B swaps sides
    if variant == "A":
        ax, mx = 14, 644
    else:
        ax, mx = 380, 14
    aw = 1010 - 630 if variant == "A" else 630
    aw = 616 if variant == "A" else 616
    ax = 14 if variant == "A" else 394
    mx = 644 if variant == "A" else 14
    mw = 366 if variant == "A" else 366
    y0, y1 = 786, 970
    d.rectangle([ax, y0, ax + aw, y1], fill=PAPER, outline=INK, width=2)
    d.text((ax + 6, y0 + 4), "ALSO ON THIS PAGE", font=AB(11), fill=ORANGE_D)
    per = (len(BRIEFS) + 2) // 3
    colw = aw // 3
    for ci, chunk in enumerate([BRIEFS[:per], BRIEFS[per:2 * per], BRIEFS[2 * per:]]):
        yy = y0 + 22
        for num, txt in chunk:
            for j, ln in enumerate(wrap(d, "%d. %s" % (num, txt), AR(8), colw - 10)[:2]):
                d.text((ax + 6 + ci * colw, yy), ln, font=AR(8), fill=INK); yy += 9
            yy += 1
    draw_map(img, mx, y0, mw, y1 - y0)
    # DATE CHECK + footer
    dc = ("DATE CHECK - NOT TODAY: 186-drone night 21-22 Nov - Alcaraz ATP title 22 Nov - "
          "Verstappen Las Vegas win 22 Nov - Wembanyama 50 pts 22 Nov - Huang RESIGNS 12 Nov - "
          "Peru quake 20 Nov - Myanmar ICJ ruling 19 Nov - Kerch Bridge strike 22 Nov.")
    d.rectangle([14, 978, 1010, 1000], outline=RED, width=2)
    for i, ln in enumerate(wrap(d, dc, AR(8), 984)[:2]):
        d.text((20, 981 + i * 10), ln, font=AR(8), fill=RED)
    d.text((14, 1004), "Sources: Reuters, AP, CNN, Times, Guardian, BBC, Treasury, CoinPaprika, IANS, KCNA. REPORTED = as reported by the named source.",
           font=AR(8), fill=GREY)
    d.text((14, 1014), "Pictures and map: original, drawn in code.", font=AB(8), fill=INK)

def build(variant, out):
    img = Image.new("RGB", (1024, 1024), IVORY)
    d = ImageDraw.Draw(img)
    header(d, variant)
    if variant == "A":
        card(img, 1, 14, 290, 996, 124, lead=True)
        card(img, 20, 14, 420, 492, 124)
        card(img, 4, 518, 420, 492, 124)
        grid = [3, 2, 5, 6, 7, 8, 9, 10, 14, 11]
        for i, k in enumerate(grid):
            r, c = divmod(i, 5)
            card(img, k, 14 + c * 200, 550 + r * 118, 192, 112)
    else:
        card(img, 20, 14, 290, 996, 124, lead=True)
        card(img, 1, 14, 420, 492, 124)
        card(img, 4, 518, 420, 492, 124)
        grid = [3, 5, 2, 7, 6, 9, 8, 14, 10, 11]
        for i, k in enumerate(grid):
            r, c = divmod(i, 5)
            card(img, k, 14 + c * 200, 550 + r * 118, 192, 112)
    bottom(img, variant)
    img.save(out, optimize=True)
    return out

if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "A"
    out = sys.argv[2] if len(sys.argv) > 2 else "entry.png"
    build(variant, out)
    print("built", variant, out, os.path.getsize(out))
