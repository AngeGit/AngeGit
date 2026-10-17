"""The spinning Earth next to the Hello, World heading, drawn from scratch so nothing borrowed ends up in
the repo (it replaces a hotlinked GIF with no licence).

A hand-traced, simplified world map (lon/lat polygons, satellite colours, hillshaded relief with the big
mountain ranges) is projected onto a tilted sphere with side light, a darker limb and a sun glint on the sea, one frame every 6 degrees, saved as an animated PNG: soft edges on light
and dark pages alike, which a GIF can't do. Seeded throughout, so the output is reproducible.

usage (from the repo root): python3 tools/globe.py assets/globe.png [size_px=44] [frames=60]
needs: pip install pillow
"""
import math, random, sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# ---------- the map: (lon, lat) polygons, traced by hand and simplified
LAND = {
    "north_america": [(-168, 65), (-165, 69), (-156, 71), (-141, 70), (-128, 70), (-115, 69), (-100, 68), (-94, 71), (-85, 70),
                      (-80, 68), (-70, 67), (-62, 60), (-56, 53), (-60, 47), (-66, 45), (-70, 42), (-74, 40), (-76, 35), (-81, 31),
                      (-80, 26), (-81, 25), (-82, 27), (-84, 30), (-89, 30), (-94, 29), (-97, 26), (-97, 21), (-95, 18), (-91, 19),
                      (-90, 21), (-87, 21), (-88, 16), (-84, 15), (-83, 10), (-79, 9), (-77, 8), (-80, 7), (-83, 8), (-86, 11),
                      (-88, 13), (-92, 14), (-96, 16), (-101, 17), (-105, 20), (-106, 23), (-110, 23), (-112, 27), (-115, 30),
                      (-117, 32), (-120, 34), (-123, 38), (-124, 42), (-124, 47), (-127, 50), (-131, 54), (-135, 58), (-140, 60),
                      (-146, 61), (-152, 59), (-158, 57), (-162, 55), (-160, 58), (-163, 60), (-166, 62)],
    "arctic_islands": [(-122, 72), (-100, 73), (-85, 73), (-80, 75), (-90, 78), (-110, 78), (-122, 76)],
    "baffin": [(-80, 63), (-72, 63), (-62, 66), (-70, 70), (-78, 73), (-90, 71), (-86, 68)],
    "greenland": [(-73, 78), (-60, 82), (-40, 83), (-22, 81), (-18, 77), (-20, 72), (-22, 70), (-30, 68), (-38, 65),
                  (-43, 60), (-48, 61), (-51, 64), (-54, 67), (-56, 72), (-62, 76)],
    "cuba": [(-85, 22), (-80, 23), (-75, 20), (-78, 20), (-82, 22)],
    "south_america": [(-77, 8), (-75, 11), (-71, 12), (-64, 11), (-60, 9), (-55, 6), (-51, 4), (-50, 0), (-45, -1), (-39, -4),
                      (-35, -6), (-35, -9), (-38, -13), (-39, -18), (-41, -22), (-45, -24), (-48, -26), (-49, -29), (-53, -33),
                      (-57, -36), (-57, -38), (-62, -39), (-65, -41), (-64, -43), (-67, -46), (-66, -48), (-69, -51), (-68, -53),
                      (-70, -55), (-73, -53), (-75, -48), (-73, -42), (-73, -37), (-71, -31), (-71, -24), (-70, -18), (-73, -16),
                      (-76, -14), (-78, -10), (-80, -6), (-81, -4), (-80, 0), (-79, 2), (-78, 4), (-77, 7)],
    "iceland": [(-24, 64), (-22, 66), (-16, 66), (-14, 65), (-18, 63), (-22, 63)],
    "uk": [(-5, 50), (1, 51), (2, 53), (0, 54), (-2, 56), (-2, 58), (-5, 58), (-6, 56), (-5, 55), (-3, 54), (-4, 53), (-5, 52)],
    "ireland": [(-10, 52), (-6, 52), (-6, 55), (-8, 55), (-10, 54)],
    "africa": [(-17, 21), (-17, 15), (-17, 12), (-15, 10), (-13, 8), (-11, 6), (-8, 4), (-4, 5), (0, 6), (3, 6), (6, 4), (9, 4),
               (9, 1), (10, -2), (12, -5), (13, -9), (12, -14), (12, -17), (14, -22), (15, -27), (17, -30), (18, -34), (20, -35),
               (23, -34), (27, -33), (30, -31), (32, -28), (33, -25), (35, -24), (35, -20), (37, -17), (40, -15), (40, -10),
               (39, -7), (39, -4), (41, -1), (43, 2), (46, 4), (49, 8), (51, 11), (48, 11), (44, 11), (43, 12), (39, 16), (37, 19),
               (36, 22), (35, 25), (33, 28), (32, 31), (30, 31), (25, 32), (20, 31), (19, 30), (15, 32), (11, 33), (10, 37),
               (5, 37), (-1, 35), (-5, 36), (-6, 35), (-9, 32), (-10, 29), (-13, 27), (-15, 25)],
    "madagascar": [(44, -25), (43, -22), (44, -17), (47, -15), (50, -15), (50, -17), (48, -22), (47, -25)],
    "eurasia": [(-9, 37), (-9, 39), (-9, 43), (-6, 44), (-2, 43), (-1, 46), (-3, 48), (-5, 48), (-2, 49), (2, 51), (4, 52), (5, 53),
                (8, 54), (8, 57), (10, 57), (10, 55), (12, 55), (14, 54), (19, 55), (21, 57), (24, 59), (29, 60), (23, 61), (21, 63),
                (25, 66), (22, 66), (17, 63), (18, 60), (16, 57), (12, 56), (11, 59), (6, 58), (5, 61), (7, 63), (13, 66), (16, 69),
                (22, 70), (28, 71), (33, 70), (41, 67), (37, 66), (44, 66), (43, 68), (53, 68), (60, 70), (66, 71), (69, 73),
                (73, 72), (80, 73), (87, 75), (97, 76), (104, 77), (113, 74), (120, 73), (130, 71), (140, 72), (150, 71),
                (160, 70), (170, 70), (180, 69), (180, 65), (178, 62), (170, 60), (163, 59), (162, 55), (156, 51), (156, 57),
                (162, 61), (155, 59), (150, 59), (143, 59), (137, 55), (141, 53), (140, 48), (135, 43), (130, 42), (128, 38),
                (127, 35), (126, 37), (124, 40), (121, 40), (118, 39), (119, 37), (121, 37), (120, 34), (122, 30), (120, 26),
                (116, 23), (111, 21), (108, 22), (106, 19), (108, 15), (109, 12), (106, 9), (105, 9), (103, 10), (100, 13),
                (99, 10), (101, 6), (103, 2), (104, 1), (101, 3), (99, 7), (98, 9), (98, 13), (97, 17), (94, 16), (94, 19),
                (91, 22), (89, 22), (87, 21), (85, 19), (81, 16), (80, 13), (80, 10), (78, 8), (77, 8), (76, 10), (73, 16),
                (72, 21), (70, 22), (68, 24), (66, 25), (62, 25), (58, 25), (57, 24), (59, 22), (57, 19), (55, 17), (52, 16),
                (48, 14), (45, 13), (43, 13), (42, 16), (39, 21), (38, 24), (35, 28), (34, 28), (35, 32), (36, 35), (36, 36),
                (32, 37), (28, 37), (26, 38), (27, 40), (29, 41), (26, 41), (24, 38), (22, 37), (21, 39), (20, 40), (19, 42),
                (16, 43), (14, 45), (12, 45), (13, 42), (15, 40), (16, 38), (18, 40), (16, 41), (12, 44), (10, 44), (8, 44),
                (6, 43), (3, 43), (3, 42), (0, 40), (-1, 38), (-2, 37), (-5, 36), (-6, 36)],
    "japan": [(130, 31), (132, 34), (135, 34), (140, 36), (141, 40), (142, 43), (145, 44), (141, 45), (140, 42), (139, 38),
              (137, 37), (133, 35), (130, 34)],
    "philippines": [(120, 18), (122, 18), (122, 14), (126, 9), (125, 6), (122, 7), (120, 12), (120, 15)],
    "sumatra": [(95, 5), (98, 4), (104, -2), (106, -6), (102, -4), (97, 1)],
    "borneo": [(109, 1), (112, 3), (117, 7), (119, 5), (118, 1), (116, -4), (111, -3), (109, -1)],
    "java": [(105, -6), (110, -7), (114, -8), (108, -8)],
    "new_guinea": [(131, -1), (135, -3), (141, -3), (147, -6), (151, -10), (146, -9), (141, -9), (138, -8), (134, -4)],
    "australia": [(114, -22), (114, -26), (115, -32), (117, -35), (123, -34), (129, -32), (134, -33), (138, -35), (140, -38),
                  (144, -38), (147, -38), (150, -37), (153, -31), (153, -26), (150, -22), (146, -19), (145, -15), (143, -11),
                  (142, -11), (141, -15), (139, -17), (136, -15), (136, -12), (132, -11), (129, -15), (126, -14), (123, -17),
                  (121, -19), (118, -20)],
    "nz_north": [(172, -35), (175, -37), (178, -38), (176, -41), (174, -42), (172, -41)],
    "nz_south": [(172, -41), (174, -42), (171, -46), (167, -46), (168, -44)],
    "antarctica": [(-180, -70), (-120, -73), (-60, -64), (0, -69), (60, -67), (120, -66), (180, -70), (180, -90), (-180, -90)],
}
WATER = {  # inland seas carved back out of the land
    "hudson_bay": [(-95, 59), (-92, 57), (-85, 55), (-80, 52), (-79, 57), (-77, 62), (-86, 64), (-94, 61)],
    "black_sea": [(28, 41), (29, 45), (33, 46), (37, 45), (41, 42), (36, 41)],
    "caspian": [(47, 45), (50, 47), (53, 45), (54, 40), (53, 37), (49, 38), (48, 42)],
    "persian_gulf": [(48, 30), (50, 27), (52, 25), (55, 25), (56, 27), (53, 27), (50, 29)],
    "baltic": [(10, 54), (14, 54), (19, 55), (21, 57), (24, 59), (29, 60), (23, 61), (21, 63), (25, 66), (22, 66), (17, 63),
               (18, 60), (16, 57), (12, 56)],
}
DESERT = {
    "sahara": [(-15, 28), (-5, 32), (10, 32), (25, 31), (32, 28), (35, 22), (30, 16), (15, 16), (0, 17), (-14, 18)],
    "arabia": [(36, 30), (46, 29), (55, 23), (52, 18), (44, 17), (38, 24)],
    "central_asia": [(55, 45), (70, 46), (90, 45), (110, 44), (115, 40), (100, 38), (80, 37), (62, 38)],
    "australia": [(117, -22), (130, -20), (140, -22), (142, -28), (135, -31), (122, -30), (118, -26)],
    "sw_america": [(-118, 36), (-106, 36), (-102, 28), (-108, 24), (-115, 30)],
    "kalahari": [(17, -20), (25, -19), (28, -25), (22, -29), (17, -26)],
    "andes": [(-71, -18), (-68, -18), (-66, -30), (-68, -45), (-70, -48), (-72, -40), (-71, -28)],
}
FOREST = {
    "amazon": [(-75, 0), (-60, 4), (-50, -1), (-45, -5), (-55, -12), (-70, -12), (-76, -6)],
    "congo": [(10, 4), (28, 4), (30, -4), (25, -8), (14, -6)],
    "taiga": [(60, 62), (100, 65), (130, 62), (140, 58), (110, 55), (80, 56)],
    "boreal": [(-140, 62), (-100, 60), (-75, 52), (-95, 50), (-125, 55)],
    "se_asia": [(98, 20), (108, 20), (108, 10), (100, 5), (97, 12)],
}
ICE = {"greenland": LAND["greenland"], "antarctica": LAND["antarctica"], "arctic": LAND["arctic_islands"]}
RIDGES = {  # mountain ranges as (lon, lat) polylines: points, width in degrees, height 0-255
    "rockies": ([(-150, 62), (-138, 60), (-128, 56), (-120, 50), (-114, 44), (-110, 40), (-107, 35), (-105, 30), (-103, 24),
                 (-99, 19)], 5, 220),
    "andes": ([(-76, 9), (-77, 3), (-78, -2), (-77, -8), (-73, -14), (-69, -18), (-68, -24), (-69, -30), (-70, -36), (-71, -42),
               (-72, -48), (-73, -52)], 4, 255),
    "himalaya": ([(68, 37), (74, 36), (80, 32), (86, 28), (92, 28), (97, 28)], 4, 255),
    "tibet": ([(80, 34), (90, 33), (97, 32)], 9, 200),
    "altai_tianshan": ([(70, 41), (78, 42), (86, 44), (92, 47), (100, 49)], 3.5, 180),
    "alps": ([(5, 44), (8, 46), (12, 47), (15, 47)], 2.5, 200),
    "atlas": ([(-9, 31), (-4, 33), (2, 35), (8, 36)], 2.5, 160),
    "caucasus_zagros": ([(40, 43), (46, 41), (48, 36), (52, 31), (57, 28)], 3, 170),
    "urals": ([(59, 50), (59, 56), (60, 62), (64, 67)], 2.5, 140),
    "scandinavia": ([(6, 59), (9, 62), (14, 66), (19, 69)], 3, 150),
    "east_africa": ([(39, 14), (38, 8), (37, 1), (36, -6), (33, -12), (30, -20)], 4, 170),
    "drakensberg": ([(26, -24), (29, -28), (28, -32)], 2.5, 120),
    "appalachians": ([(-86, 33), (-81, 37), (-77, 40), (-72, 44), (-68, 47)], 3, 130),
    "brazilian_highlands": ([(-50, -12), (-45, -18), (-44, -22)], 6, 90),
    "great_dividing": ([(145, -14), (147, -20), (150, -27), (151, -33), (147, -38)], 2.5, 130),
    "east_siberia": ([(130, 62), (140, 65), (155, 63), (160, 58)], 4, 120),
    "greenland_dome": ([(-45, 63), (-42, 72), (-40, 80)], 10, 140),
}

OCEAN, OCEAN_DEEP = (58, 104, 136), (30, 62, 94)  # steel blue, like satellite imagery
LAND_C, DESERT_C, FOREST_C, ICE_C = (132, 128, 88), (204, 182, 136), (82, 106, 60), (236, 238, 236)

TW, TH = 1440, 720  # equirectangular texture: 4 px per degree


PAD = TW // 8  # drawn wider than one turn, so blurs wrap round the date line without a seam


def to_tex(lon, lat, shift=0):
    return ((lon + 180 + shift) / 360 * TW + PAD, (90 - lat) / 180 * TH)


def polys(layer):
    """Every polygon three times (one turn either side), so shapes crossing the edges wrap round."""
    for poly in layer.values():
        for shift in (-360, 0, 360):
            yield [to_tex(lon, lat, shift) for lon, lat in poly]


def heightmap(W):
    """Fractal relief (seeded value noise, four octaves) plus the big mountain ranges, on the padded canvas."""
    rnd = random.Random(11)
    noise = Image.new("L", (TW, TH), 128)
    for cells, weight in ((12, .5), (24, .4), (48, .3), (96, .15)):
        small = Image.frombytes("L", (cells, cells // 2), rnd.randbytes(cells * cells // 2))
        noise = Image.blend(noise, small.resize((TW, TH), Image.BICUBIC), weight)
    relief = Image.new("L", (W, TH))
    for shift in (-TW, 0, TW):
        relief.paste(noise, (PAD + shift, 0))
    ridges = Image.new("L", (W, TH), 0)
    rd = ImageDraw.Draw(ridges)
    for pts, width_deg, height in RIDGES.values():
        for shift in (-360, 0, 360):
            rd.line([to_tex(lon, lat, shift) for lon, lat in pts], fill=height, width=round(width_deg * TW / 360), joint="curve")
    ridges = ridges.filter(ImageFilter.GaussianBlur(14))
    return ImageChops.add(Image.eval(relief, lambda v: v // 2), ridges).filter(ImageFilter.GaussianBlur(3))


def texture():
    rnd = random.Random(3)
    W = TW + 2 * PAD
    ocean = Image.new("RGB", (W, TH))
    od = ImageDraw.Draw(ocean)
    for y in range(TH):  # a touch lighter in the tropics, like shallow warm seas
        t = abs(y / TH - .5) * 2
        od.line([(0, y), (W, y)], fill=tuple(round(a + (b - a) * t * .7) for a, b in zip(OCEAN, OCEAN_DEEP)))
    mask = Image.new("L", (W, TH), 0)
    md = ImageDraw.Draw(mask)
    for poly in polys(LAND):
        md.polygon(poly, fill=255)
    for poly in polys(WATER):
        md.polygon(poly, fill=0)
    land = Image.new("RGB", (W, TH), LAND_C)
    ld = ImageDraw.Draw(land)
    for colour, layer in ((DESERT_C, DESERT), (FOREST_C, FOREST), (ICE_C, ICE)):
        for poly in polys(layer):
            ld.polygon(poly, fill=colour)
    land = land.filter(ImageFilter.GaussianBlur(6))  # biomes blend into each other
    noise = Image.frombytes("L", (W, TH), random.Random(5).randbytes(W * TH)).filter(ImageFilter.GaussianBlur(1.2))  # terrain grain
    land = Image.composite(land, Image.blend(land, Image.merge("RGB", [noise] * 3), .18), Image.new("L", (W, TH), 220))
    # chiaroscuro: hillshade lit from the north-west (slopes facing it brighten, the others fall into shade)
    shade = heightmap(W).filter(ImageFilter.Kernel((3, 3), [-2, -1, 0, -1, 0, 1, 0, 1, 2], scale=.45, offset=128))
    land = Image.blend(land, ImageChops.hard_light(land, Image.merge("RGB", [shade] * 3)), .75)
    tex = Image.composite(land, ocean, mask.filter(ImageFilter.GaussianBlur(1.5)))
    clouds = Image.new("L", (W, TH), 0)
    cd = ImageDraw.Draw(clouds)
    for _ in range(12):  # a few cloud systems: clusters of puffs, not streaks
        cx, cy = rnd.uniform(0, TW), rnd.uniform(TH * .15, TH * .85)
        for _ in range(rnd.randint(5, 10)):
            px, py = cx + rnd.uniform(-45, 45), cy + rnd.uniform(-14, 14)
            w, h = rnd.uniform(10, 34), rnd.uniform(5, 13)
            for shift in (-TW, 0, TW):
                cd.ellipse((px + PAD + shift - w, py - h, px + PAD + shift + w, py + h), fill=rnd.randint(25, 60))
    tex = Image.composite(Image.new("RGB", (W, TH), (238, 242, 246)), tex, clouds.filter(ImageFilter.GaussianBlur(5)))
    return tex.crop((PAD, 0, PAD + TW, TH)), mask.crop((PAD, 0, PAD + TW, TH))


def frames(size, count, tilt=18):
    """Orthographic Earth, tilted towards the viewer, one frame per 360/count degrees, RGBA."""
    tex_img, land_img = texture()
    tex, land = tex_img.load(), land_img.load()
    ss = size * 3  # supersampled, then reduced for soft edges
    r = ss / 2 - ss * .06  # room for the atmosphere glow
    c = ss / 2
    phi0 = math.radians(tilt)
    light = (-.45, .4, .8)
    ln = math.sqrt(sum(v * v for v in light))
    light = tuple(v / ln for v in light)
    half = (light[0], light[1], light[2] + 1)  # halfway between the light and the viewer, for the glint
    hn = math.sqrt(sum(v * v for v in half))
    half = tuple(v / hn for v in half)
    pix = []  # per pixel: (lat, lon offset, shade, nz, glint) or None, computed once
    for y in range(ss):
        for x in range(ss):
            nx, ny = (x + .5 - c) / r, (c - y - .5) / r
            rho = math.hypot(nx, ny)
            if rho >= 1:
                pix.append((None, rho))
                continue
            nz = math.sqrt(1 - rho * rho)
            cc = math.asin(rho)
            lat = math.degrees(math.asin(math.cos(cc) * math.sin(phi0) + (ny * math.sin(cc) * math.cos(phi0) / rho if rho else 0)))
            dlon = math.degrees(math.atan2(nx * math.sin(cc), rho * math.cos(cc) * math.cos(phi0) - ny * math.sin(cc) * math.sin(phi0)))
            lam = max(0., nx * light[0] + ny * light[1] + nz * light[2])
            shade = .2 + .92 * lam ** .85
            glint = max(0., nx * half[0] + ny * half[1] + nz * half[2]) ** 48 * 90
            pix.append(((lat, dlon, shade, nz, glint), rho))
    out = []
    for f in range(count):
        lon0 = -180 + 360 * f / count
        img = Image.new("RGBA", (ss, ss))
        data = []
        for p, rho in pix:
            if p is None:  # atmosphere: a thin blue glow fading out past the limb
                a = max(0., 1 - (rho - 1) / .05)
                data.append((140, 180, 230, round(70 * a * a)))
                continue
            lat, dlon, shade, nz, glint = p
            u = int(((lon0 + dlon + 180) % 360) / 360 * TW) % TW
            v = min(TH - 1, int((90 - lat) / 180 * TH))
            cr, cg, cb = tex[u, v]
            sea = glint * (255 - land[u, v]) / 255  # the sun's reflection only on water
            rim = (1 - nz) ** 3 * .2  # a little haze towards the edge
            data.append((min(255, round(cr * shade + 120 * rim + sea)), min(255, round(cg * shade + 170 * rim + sea)),
                         min(255, round(cb * shade + 255 * rim + sea)), 255))
        img.putdata(data)
        out.append(img.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA"))
    return out


def main():
    path = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 44
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    imgs = frames(size, count)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=round(9000 / count), loop=0, disposal=1, blend=0)
    print(path, size, "px", count, "frames")


if __name__ == "__main__":
    main()
