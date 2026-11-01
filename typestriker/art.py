"""Every sprite in the game, drawn in code.

Sprites are drawn at 4x size and scaled down, which gives smooth edges without
any image files. Ships are drawn nose-up; enemies are flipped to face the player.
"""
import functools
import math
import random

import pygame

SS = 4


def shade(col, f):
    return tuple(max(0, min(255, int(c * f))) for c in col[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


@functools.lru_cache(maxsize=256)
def radial(radius, col, power=2.0):
    """A round glow with real alpha."""
    size = max(2, radius * 2)
    base = pygame.Surface((64, 64), pygame.SRCALPHA)
    for r in range(32, 0, -1):
        alpha = int(255 * (1 - r / 32) ** power)
        pygame.draw.circle(base, (*col[:3], alpha), (32, 32), r)
    return pygame.transform.smoothscale(base, (size, size))


def dim(col, k):
    """Scale a colour in fixed steps, so glows can share cached sprites."""
    return shade(col, round(max(0.0, min(1.0, k)) * 8) / 8)


@functools.lru_cache(maxsize=1024)
def additive(radius, col, power=2.0):
    """A round glow on black, meant for BLEND_RGB_ADD."""
    size = max(2, radius * 2)
    base = pygame.Surface((64, 64))
    for r in range(32, 0, -1):
        k = (1 - r / 32) ** power
        pygame.draw.circle(base, tuple(int(c * k) for c in col[:3]), (32, 32), r)
    return pygame.transform.smoothscale(base, (size, size))


class Pen:
    def __init__(self, w, h, k=1.0):
        self.w, self.h, self.k = w, h, k
        self.u = SS * k
        self.cx = w / 2
        self.surf = pygame.Surface((int(w * self.u), int(h * self.u)), pygame.SRCALPHA)

    def _p(self, pts):
        return [(x * self.u, y * self.u) for x, y in pts]

    def poly(self, pts, col, outline=None, width=0.7):
        pygame.draw.polygon(self.surf, col, self._p(pts))
        if outline:
            pygame.draw.polygon(self.surf, outline, self._p(pts), max(1, int(width * self.u)))

    def sym(self, half, col, outline=(14, 18, 30), width=0.7, contrast=0.2):
        """Mirror a half outline about the centre. The left side catches the light."""
        left = [(self.cx - x, y) for x, y in half]
        right = [(self.cx + x, y) for x, y in half]
        self.poly(left, shade(col, 1 + contrast), outline, width)
        self.poly(right, shade(col, 1 - contrast), outline, width)

    def circle(self, x, y, r, col, outline=None, width=0.7):
        c = (x * self.u, y * self.u)
        pygame.draw.circle(self.surf, col, c, r * self.u)
        if outline:
            pygame.draw.circle(self.surf, outline, c, r * self.u, max(1, int(width * self.u)))

    def both(self, dx, y, r, col, outline=None):
        self.circle(self.cx - dx, y, r, col, outline)
        self.circle(self.cx + dx, y, r, col, outline)

    def ellipse(self, x, y, rx, ry, col, outline=None, width=0.7):
        rect = pygame.Rect(0, 0, int(rx * 2 * self.u), int(ry * 2 * self.u))
        rect.center = (int(x * self.u), int(y * self.u))
        pygame.draw.ellipse(self.surf, col, rect)
        if outline:
            pygame.draw.ellipse(self.surf, outline, rect, max(1, int(width * self.u)))

    def line(self, a, b, col, width=0.7):
        pygame.draw.line(self.surf, col, (a[0] * self.u, a[1] * self.u),
                         (b[0] * self.u, b[1] * self.u), max(1, int(width * self.u)))

    def rect(self, x, y, w, h, col, radius=0, outline=None):
        r = pygame.Rect(int(x * self.u), int(y * self.u), int(w * self.u), int(h * self.u))
        pygame.draw.rect(self.surf, col, r, border_radius=int(radius * self.u))
        if outline:
            pygame.draw.rect(self.surf, outline, r, max(1, int(0.7 * self.u)), border_radius=int(radius * self.u))

    def glow(self, x, y, r, col, power=1.6):
        g = radial(int(r * self.u), col, power)
        self.surf.blit(g, (x * self.u - g.get_width() / 2, y * self.u - g.get_height() / 2))

    def glass(self, x, y, rx, ry, col=(90, 220, 255)):
        self.ellipse(x, y, rx, ry, shade(col, 0.45), (12, 16, 28))
        self.ellipse(x, y + ry * 0.12, rx * 0.78, ry * 0.78, col)
        self.ellipse(x - rx * 0.28, y - ry * 0.32, rx * 0.3, ry * 0.32, (235, 250, 255))

    def done(self, flip=False):
        out = pygame.transform.smoothscale(self.surf, (int(self.w * self.k), int(self.h * self.k)))
        return pygame.transform.flip(out, False, True) if flip else out


OUT = (14, 18, 30)

# ---- Player ---------------------------------------------------------------


def player_ship(k=1.0):
    p = Pen(76, 92, k)
    white, steel, orange = (222, 232, 245), (120, 142, 178), (255, 140, 50)
    # Engine flames are added at draw time. Wings first.
    p.sym([(8, 42), (35, 68), (37, 80), (26, 78), (8, 72)], steel)
    p.sym([(12, 50), (31, 69), (32, 74), (12, 66)], orange, None)
    # Wing cannons
    p.sym([(30, 40), (33, 40), (34, 72), (29, 72)], white)
    # Tail fins
    p.sym([(6, 62), (17, 84), (17, 88), (6, 80)], (70, 96, 150))
    # Fuselage
    p.sym([(0, 2), (4, 12), (9, 36), (12, 62), (10, 82), (0, 84)], white)
    p.sym([(0, 46), (6, 52), (8, 78), (0, 80)], steel, None)
    # Nose stripe and spine
    p.sym([(0, 2), (4, 12), (5.5, 20), (0, 16)], orange, None)
    p.line((p.cx, 44), (p.cx, 80), (40, 52, 80), 0.6)
    p.glass(p.cx, 32, 5.5, 11)
    # Engine bells
    p.rect(p.cx - 9, 80, 7, 6, (60, 70, 92), 1.5, OUT)
    p.rect(p.cx + 2, 80, 7, 6, (60, 70, 92), 1.5, OUT)
    return p.done()


# ---- Small enemies --------------------------------------------------------


def _scout(pal):
    p = Pen(60, 58)
    p.sym([(6, 26), (28, 44), (24, 52), (6, 44)], pal.secondary)
    p.sym([(0, 2), (7, 20), (11, 42), (6, 54), (0, 54)], pal.primary)
    p.sym([(0, 2), (3, 12), (0, 16)], pal.accent, None)
    p.glass(p.cx, 28, 4, 7, pal.accent)
    p.both(24, 48, 3, pal.accent, OUT)
    return p.done(True)


def _fighter(pal):
    p = Pen(78, 72)
    p.sym([(8, 34), (38, 14), (36, 30), (24, 44), (10, 56)], pal.secondary)
    p.sym([(26, 24), (37, 16), (36, 28), (28, 36)], pal.accent, None)
    p.sym([(0, 4), (6, 16), (11, 40), (12, 60), (6, 68), (0, 68)], pal.primary)
    p.sym([(4, 58), (11, 58), (10, 66), (4, 68)], shade(pal.secondary, 0.7), None)
    p.glass(p.cx, 30, 5, 9, pal.accent)
    p.line((p.cx - 22, 30), (p.cx - 11, 46), OUT)
    p.line((p.cx + 22, 30), (p.cx + 11, 46), OUT)
    return p.done(True)


def _bomber(pal):
    p = Pen(112, 78)
    p.sym([(0, 12), (20, 18), (54, 44), (52, 54), (32, 52), (22, 66), (0, 70)], pal.primary)
    p.sym([(20, 24), (48, 44), (34, 46), (20, 38)], pal.secondary, None)
    for dx in (14, 26, 38):
        p.both(dx, 54, 4.5, shade(pal.secondary, 0.6), OUT)
        p.both(dx, 54, 2.2, pal.accent)
    p.sym([(0, 12), (7, 18), (7, 34), (0, 40)], pal.secondary, None)
    p.glass(p.cx, 24, 5, 6, pal.accent)
    p.line((p.cx, 40), (p.cx, 70), OUT)
    return p.done(True)


def _saucer(pal):
    p = Pen(84, 62)
    p.ellipse(p.cx, 34, 41, 24, shade(pal.secondary, 0.8), OUT)
    p.ellipse(p.cx, 31, 40, 22, pal.primary, OUT)
    p.ellipse(p.cx - 2, 27, 31, 14, shade(pal.primary, 1.25))
    for i in range(10):
        angle = i / 10 * math.tau
        p.circle(p.cx + math.cos(angle) * 34, 32 + math.sin(angle) * 17, 2.6, pal.accent, OUT)
    p.ellipse(p.cx, 30, 18, 13, shade(pal.secondary, 0.6), OUT)
    p.glass(p.cx, 28, 13, 10, pal.accent)
    return p.done()


def _interceptor(pal):
    p = Pen(70, 88)
    p.sym([(5, 44), (32, 72), (33, 84), (24, 78), (5, 66)], pal.secondary)
    p.sym([(5, 34), (17, 12), (20, 14), (9, 50)], pal.secondary)
    p.sym([(0, 2), (4, 24), (7, 60), (5, 82), (0, 84)], pal.primary)
    p.sym([(22, 66), (32, 74), (33, 82), (24, 76)], pal.accent, None)
    p.both(18, 13, 2, pal.accent)
    p.glass(p.cx, 36, 3.5, 9, pal.accent)
    return p.done(True)


def _drone(pal):
    p = Pen(70, 70)
    for angle in (45, 135, 225, 315):
        rad = math.radians(angle)
        x, y = p.cx + math.cos(rad) * 24, 35 + math.sin(rad) * 24
        p.line((p.cx, 35), (x, y), shade(pal.secondary, 0.8), 4.5)
        p.line((p.cx, 35), (x, y), pal.secondary, 2.5)
        p.circle(x, y, 9.5, shade(pal.secondary, 0.6), OUT)
        p.circle(x, y, 7, (20, 24, 36, 255))
        p.line((x - 6, y - 3), (x + 6, y + 3), pal.primary, 1)
        p.line((x + 3, y - 6), (x - 3, y + 6), pal.primary, 1)
    hexagon = [(p.cx + math.cos(i / 6 * math.tau) * 15, 35 + math.sin(i / 6 * math.tau) * 15)
               for i in range(6)]
    p.poly(hexagon, pal.primary, OUT)
    p.circle(p.cx, 35, 8.5, shade(pal.secondary, 0.5), OUT)
    p.circle(p.cx, 35, 5.5, pal.accent)
    p.circle(p.cx - 1.6, 33.4, 1.6, (255, 255, 255))
    return p.done()


def tank_hull(pal):
    p = Pen(62, 74)
    # Tracks
    for x in (2, 46):
        p.rect(x, 5, 14, 64, (34, 34, 38), 3, OUT)
        for y in range(8, 68, 6):
            p.rect(x + 1.5, y, 11, 3, (70, 70, 76), 0.6)
    # Body
    p.rect(13, 9, 36, 56, shade(pal.primary, 0.85), 4, OUT)
    p.rect(16, 12, 30, 50, pal.primary, 3)
    p.poly([(16, 12), (46, 12), (42, 22), (20, 22)], shade(pal.primary, 1.25))
    p.poly([(16, 62), (46, 62), (42, 54), (20, 54)], shade(pal.primary, 0.65))
    p.rect(19, 56, 8, 4, pal.accent, 1)
    p.rect(35, 56, 8, 4, pal.accent, 1)
    return p.done()


def tank_turret(pal):
    """Barrel pointing up. The centre of rotation is the middle of the surface."""
    p = Pen(44, 92)
    p.rect(p.cx - 2.7, 4, 5.4, 42, shade(pal.secondary, 0.8), 1, OUT)
    p.rect(p.cx - 3.8, 3, 7.6, 9, shade(pal.secondary, 0.5), 1, OUT)
    p.circle(p.cx, 46, 16, shade(pal.secondary, 0.75), OUT)
    p.circle(p.cx - 1.5, 44.5, 13.5, pal.secondary)
    p.circle(p.cx - 5, 40, 3.3, shade(pal.secondary, 1.5))
    p.circle(p.cx + 6, 50, 2.6, pal.accent, OUT)
    return p.done()


def missile_sprite(pal):
    p = Pen(26, 64)
    p.sym([(4, 44), (11, 56), (11, 62), (4, 56)], (170, 44, 44))
    p.sym([(0, 2), (4, 12), (5, 54), (0, 56)], (214, 218, 228))
    p.sym([(0, 2), (4, 12), (4.6, 18), (0, 18)], (226, 50, 50), None)
    p.sym([(0, 28), (5, 28), (5, 34), (0, 34)], pal.accent, None)
    p.rect(p.cx - 3, 54, 6, 5, (50, 52, 62), 1, OUT)
    return p.done(True)


def asteroid_sprite(size, seed, tint):
    """A lumpy rock lit from the upper left, with craters and speckle."""
    rng = random.Random(seed)
    p = Pen(size, size)
    c = size / 2
    n = 16
    radii = [size * 0.36 + rng.uniform(-size * 0.07, size * 0.11) for _ in range(n)]
    outline = [(c + math.cos(i / n * math.tau) * radii[i], c + math.sin(i / n * math.tau) * radii[i])
               for i in range(n)]
    p.poly(outline, shade(tint, 0.42))
    mask = pygame.Surface(p.surf.get_size(), pygame.SRCALPHA)
    mask.blit(p.surf, (0, 0))
    # Overlapping tones build up a rounded look
    for f, off, scale in ((0.62, -0.06, 0.92), (0.82, -0.12, 0.74), (1.02, -0.18, 0.52), (1.2, -0.23, 0.28)):
        pts = [(c + off * size + (x - c) * scale, c + off * size + (y - c) * scale) for x, y in outline]
        p.poly(pts, shade(tint, f))
    for _ in range(size // 9 + 3):
        a, d = rng.uniform(0, math.tau), rng.uniform(0, size * 0.32)
        x, y, r = c + math.cos(a) * d, c + math.sin(a) * d, rng.uniform(size * 0.02, size * 0.09)
        p.circle(x + r * 0.15, y + r * 0.15, r * 1.15, shade(tint, 1.05))
        p.circle(x, y, r, shade(tint, 0.45))
    for _ in range(size * 3):
        a, d = rng.uniform(0, math.tau), rng.uniform(0, size * 0.42)
        p.circle(c + math.cos(a) * d, c + math.sin(a) * d, rng.uniform(0.2, 0.7),
                 shade(tint, rng.uniform(0.45, 1.25)))
    p.surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return p.done()


# ---- Bosses ---------------------------------------------------------------

def _engine_row(p, y, dxs, r, col):
    for dx in dxs:
        p.both(dx, y, r, shade(col, 0.4), OUT)
        p.both(dx, y, r * 0.62, col)


def _boss_warden():
    p = Pen(260, 140)
    a, b, g = (108, 138, 188), (52, 72, 122), (120, 230, 255)
    p.sym([(40, 40), (130, 20), (124, 66), (70, 80), (40, 90)], b)
    p.sym([(84, 38), (128, 26), (122, 56), (88, 64)], a)
    p.sym([(0, 6), (24, 16), (46, 50), (40, 110), (20, 128), (0, 132)], a)
    p.sym([(0, 22), (16, 30), (28, 58), (20, 92), (0, 104)], b)
    _engine_row(p, 50, (66, 104), 8, g)
    for dx in (96, 116):
        p.sym([(dx - 5, 58), (dx + 5, 56), (dx + 3, 82), (dx - 3, 82)], (210, 220, 236))
    p.glass(p.cx, 60, 12, 18, g)
    return p.done(True)


def _boss_rockbreaker():
    p = Pen(270, 150)
    a, b, g = (190, 130, 70), (96, 66, 48), (255, 190, 70)
    # Drill arms
    for sign in (-1, 1):
        x = p.cx + sign * 100
        p.poly([(x - 20, 76), (x + 20, 76), (x, 4)], (176, 180, 190), OUT)
        for t in (0.2, 0.4, 0.6, 0.8):
            y = 76 - 72 * t
            w = 20 * (1 - t)
            p.line((x - w, y + 5), (x + w, y - 5), (72, 76, 90), 1.6)
        p.rect(x - 24, 74, 48, 22, b, 3, OUT)
        p.rect(x - 18, 78, 36, 6, g, 1)
    p.sym([(64, 86), (88, 84), (88, 92), (64, 96)], (90, 90, 100))
    # Main body
    p.sym([(0, 36), (42, 44), (72, 74), (68, 120), (34, 142), (0, 146)], a)
    p.sym([(0, 54), (28, 60), (48, 84), (40, 112), (0, 124)], b)
    for dx, y in ((0, 112), (30, 96)):
        p.both(dx, y, 7, (60, 44, 36), OUT)
        p.both(dx, y, 4, g)
    # Rock lumps stuck on the hull
    rock = (116, 96, 84)
    for dx, y, r in ((50, 118, 11), (60, 88, 7), (22, 134, 9)):
        p.both(dx, y, r, rock, OUT)
        p.both(dx + 1, y - 2, r * 0.55, shade(rock, 1.35))
    p.glass(p.cx, 76, 14, 14, g)
    return p.done(True)


def _boss_crawler():
    p = Pen(250, 180)
    a, b, g = (96, 124, 66), (58, 80, 46), (240, 230, 90)
    for x in (2, 206):
        p.rect(x, 8, 42, 164, (32, 32, 36), 8, OUT)
        for y in range(14, 168, 11):
            p.rect(x + 4, y, 34, 5, (74, 74, 80), 1)
    p.rect(40, 18, 170, 144, b, 8, OUT)
    p.rect(48, 26, 154, 128, a, 6)
    p.poly([(48, 26), (202, 26), (186, 44), (64, 44)], shade(a, 1.3))
    p.poly([(48, 154), (202, 154), (186, 138), (64, 138)], shade(a, 0.6))
    # Camouflage patches
    for x, y, r in ((74, 62, 12), (172, 62, 14), (90, 128, 12), (160, 122, 10), (70, 100, 8), (182, 98, 8)):
        p.circle(x, y, r, b)
    # Three turrets, barrels pointing down in the final flipped sprite
    for x, y, r, length in ((125, 92, 30, 74), (72, 54, 16, 44), (178, 54, 16, 44)):
        p.rect(x - r * 0.2, y - length, r * 0.4, length, (46, 52, 40), 1, OUT)
        p.circle(x, y, r, shade(b, 0.8), OUT)
        p.circle(x - 2, y - 2, r * 0.82, b)
        p.circle(x, y, r * 0.38, g, OUT)
    return p.done(True)


def _boss_manta():
    p = Pen(290, 150)
    a, b, g = (196, 58, 84), (104, 32, 70), (255, 170, 120)
    p.sym([(0, 30), (40, 34), (100, 18), (142, 40), (118, 78), (70, 96), (34, 124), (0, 142)], a)
    p.sym([(0, 46), (32, 50), (86, 40), (116, 50), (94, 72), (56, 84), (26, 106), (0, 122)], b)
    # Wing veins
    for t in (0.3, 0.5, 0.7):
        for sign in (-1, 1):
            p.line((p.cx + sign * 20, 70), (p.cx + sign * 130 * t, 40 + 46 * t), g, 0.9)
    p.sym([(26, 28), (34, 2), (44, 6), (42, 34)], a)
    _engine_row(p, 70, (54, 84), 6, g)
    p.glow(p.cx, 76, 30, g)
    p.circle(p.cx, 76, 13, (60, 20, 40), OUT)
    p.circle(p.cx, 76, 9, g)
    p.ellipse(p.cx, 76, 2.5, 8, (40, 10, 20))
    return p.done(True)


def _boss_scorpion():
    p = Pen(280, 190)
    a, b, g = (214, 166, 84), (126, 86, 48), (255, 90, 50)
    # Legs
    for i, y in enumerate((96, 112, 128)):
        for sign in (-1, 1):
            knee = (p.cx + sign * (84 + i * 6), y - 14)
            foot = (p.cx + sign * (112 + i * 8), y + 22)
            p.line((p.cx + sign * 34, y), knee, OUT, 5)
            p.line((p.cx + sign * 34, y), knee, b, 3)
            p.line(knee, foot, OUT, 4)
            p.line(knee, foot, a, 2.2)
    # Claws, at the bottom of the flipped sprite so they lead the attack
    for sign in (-1, 1):
        p.line((p.cx + sign * 34, 70), (p.cx + sign * 84, 40), OUT, 10)
        p.line((p.cx + sign * 34, 70), (p.cx + sign * 84, 40), a, 7)
        cx, cy = p.cx + sign * 96, 26
        p.poly([(cx - 22 * sign, cy + 20), (cx - 26 * sign, cy - 20), (cx - 4 * sign, cy - 12), (cx - 2 * sign, cy + 4)],
               shade(a, 1.1), OUT)
        p.poly([(cx - 22 * sign, cy + 20), (cx + 24 * sign, cy - 18), (cx + 16 * sign, cy + 18)], b, OUT)
    # Tail: segments climbing to a stinger
    for i in range(6):
        y = 136 + i * 8
        r = 16 - i * 1.5
        p.circle(p.cx, y, r, shade(a, 1 - i * 0.05), OUT)
    p.poly([(p.cx - 7, 178), (p.cx + 7, 178), (p.cx, 189)], g, OUT)
    # Armoured body
    p.sym([(0, 54), (30, 62), (46, 90), (38, 126), (0, 146)], a)
    for y in (84, 104, 124):
        p.line((p.cx - 34, y), (p.cx + 34, y), b, 1.4)
    p.both(14, 68, 7, (40, 16, 12), OUT)
    p.both(14, 68, 4.4, g)
    return p.done(True)


def _boss_frost():
    p = Pen(250, 170)
    a, b, g = (186, 226, 248), (84, 132, 182), (90, 240, 255)
    rng = random.Random(6)
    # Ice spikes around the rim
    for i in range(14):
        ang = i / 14 * math.tau
        length = rng.uniform(70, 84)
        x, y = 125 + math.cos(ang) * length * 1.34, 85 + math.sin(ang) * length
        side = ang + math.pi / 2
        bx, by = 125 + math.cos(ang) * 58 * 1.1, 85 + math.sin(ang) * 58 * 0.9
        pts = [(x, y), (bx + math.cos(side) * 13, by + math.sin(side) * 13),
               (bx - math.cos(side) * 13, by - math.sin(side) * 13)]
        p.poly(pts, shade(a, rng.uniform(0.72, 1.05)), (50, 84, 130))
    hexagon = [(125 + math.cos(i / 6 * math.tau) * 72, 85 + math.sin(i / 6 * math.tau) * 60) for i in range(6)]
    p.poly(hexagon, b, OUT)
    inner = [(125 + math.cos(i / 6 * math.tau) * 54, 85 + math.sin(i / 6 * math.tau) * 44) for i in range(6)]
    for i in range(6):
        t = [inner[i], inner[(i + 1) % 6], (125, 85)]
        p.poly(t, mix(a, b, 0.2 + 0.13 * i), (60, 96, 146))
    for i in range(6):
        p.circle(hexagon[i][0], hexagon[i][1], 6, g, OUT)
    p.glow(125, 85, 34, g)
    p.circle(125, 85, 15, (24, 70, 110), OUT)
    p.circle(125, 85, 10, g)
    p.circle(122, 82, 3.5, (255, 255, 255))
    return p.done(True)


def _boss_stormlord():
    p = Pen(250, 190)
    a, b, g = (70, 196, 180), (56, 74, 130), (214, 130, 255)
    cx, cy = 125, 95
    p.circle(cx, cy, 88, b, OUT)
    p.circle(cx, cy, 72, (14, 16, 34, 255), OUT)
    # Coils on the ring
    for i in range(8):
        ang = i / 8 * math.tau
        x, y = cx + math.cos(ang) * 80, cy + math.sin(ang) * 80
        p.circle(x, y, 17, shade(a, 0.5), OUT)
        p.circle(x, y, 12, a, OUT)
        p.circle(x - 2, y - 2, 4, (220, 255, 250))
    # Lightning arms to the orb
    rng = random.Random(4)
    for i in range(8):
        ang = i / 8 * math.tau
        pts = []
        for t in range(6):
            d = 22 + t * 10
            jitter = rng.uniform(-0.2, 0.2) if 0 < t < 5 else 0
            pts.append((cx + math.cos(ang + jitter) * d, cy + math.sin(ang + jitter) * d))
        for u, v in zip(pts, pts[1:]):
            p.line(u, v, g, 1.3)
    p.glow(cx, cy, 44, g)
    p.circle(cx, cy, 22, shade(g, 0.55), OUT)
    p.circle(cx, cy, 16, g)
    p.circle(cx - 5, cy - 5, 6, (255, 240, 255))
    return p.done(True)


def _boss_titan():
    p = Pen(280, 190)
    a, _, g = (70, 56, 54), (40, 32, 34), (255, 130, 30)

    def rock(cx, cy, rx, ry, seed):
        rng = random.Random(seed)
        pts = []
        for i in range(10):
            ang = i / 10 * math.tau
            f = rng.uniform(0.86, 1.1)
            pts.append((cx + math.cos(ang) * rx * f, cy + math.sin(ang) * ry * f))
        p.poly(pts, a, OUT)
        p.poly([(cx + (x - cx) * 0.72 - rx * 0.1, cy + (y - cy) * 0.72 - ry * 0.12) for x, y in pts], shade(a, 1.3))

    # Arms and fists
    for sign, seed in ((-1, 1), (1, 2)):
        rock(p.cx + sign * 88, 76, 30, 26, seed)
        rock(p.cx + sign * 108, 38, 26, 24, seed + 2)
        p.line((p.cx + sign * 88, 76), (p.cx + sign * 108, 38), g, 2)
        p.line((p.cx + sign * 46, 96), (p.cx + sign * 88, 76), g, 2)
    rock(p.cx, 102, 72, 68, 7)
    rock(p.cx, 162, 40, 26, 9)
    # Lava cracks
    rng = random.Random(12)
    for i in range(9):
        ang = i / 9 * math.tau
        x, y = p.cx, 96
        for _ in range(5):
            nx = x + math.cos(ang) * 13 + rng.uniform(-5, 5)
            ny = y + math.sin(ang) * 11 + rng.uniform(-5, 5)
            p.line((x, y), (nx, ny), g, 2.2)
            p.line((x, y), (nx, ny), (255, 220, 120), 0.8)
            x, y = nx, ny
    p.glow(p.cx, 96, 36, g)
    p.circle(p.cx, 96, 14, (255, 190, 70), OUT)
    p.circle(p.cx, 96, 8, (255, 250, 220))
    return p.done(True)


def _boss_hive():
    p = Pen(270, 180)
    a, b, g = (112, 96, 156), (58, 50, 92), (120, 255, 150)
    cx, cy = 135, 90
    # Armoured petals
    for i in range(10):
        ang = i / 10 * math.tau
        side = ang + math.pi / 2
        tip = (cx + math.cos(ang) * 130, cy + math.sin(ang) * 88)
        base = (cx + math.cos(ang) * 50, cy + math.sin(ang) * 40)
        w = 26
        pts = [tip, (base[0] + math.cos(side) * w, base[1] + math.sin(side) * w),
               (base[0] - math.cos(side) * w, base[1] - math.sin(side) * w)]
        p.poly(pts, shade(a, 0.8 + 0.08 * (i % 3)), OUT)
        mid = (cx + math.cos(ang) * 92, cy + math.sin(ang) * 63)
        p.circle(mid[0], mid[1], 5.5, g, OUT)
    # Honeycomb body
    p.ellipse(cx, cy, 76, 62, b, OUT)
    for row in range(-2, 3):
        for col in range(-3, 4):
            x = cx + col * 20 + (row % 2) * 10
            y = cy + row * 17
            if ((x - cx) / 72) ** 2 + ((y - cy) / 56) ** 2 < 1:
                hexagon = [(x + math.cos(i / 6 * math.tau + 0.52) * 10, y + math.sin(i / 6 * math.tau + 0.52) * 10)
                           for i in range(6)]
                p.poly(hexagon, a, shade(b, 0.6))
    p.glow(cx, cy, 42, g)
    p.circle(cx, cy, 25, (22, 36, 34), OUT)
    p.circle(cx, cy, 19, g)
    p.circle(cx, cy, 9, (10, 30, 16))
    p.circle(cx - 3, cy - 3, 3, (235, 255, 240))
    return p.done(True)


def _boss_emperor():
    p = Pen(320, 190)
    a, b, g = (66, 44, 110), (28, 20, 52), (255, 90, 220)
    # Great swept wings
    p.sym([(44, 70), (158, 8), (140, 70), (152, 74), (120, 112), (128, 118), (70, 138), (40, 130)], b, (120, 60, 170), 1)
    p.sym([(60, 76), (138, 28), (124, 72), (98, 100), (60, 116)], a, None)
    for dx, y in ((118, 56), (100, 74), (82, 92)):
        p.both(dx, y, 6, b, g)
        p.both(dx, y, 3, g)
    # Crown spikes at the back
    for dx, h in ((0, 0), (20, 8), (40, 22)):
        p.sym([(dx - 9, 44 + h), (dx, 2 + h), (dx + 9, 44 + h)], a, (120, 60, 170), 1, 0.1)
    # Core hull
    p.sym([(0, 34), (40, 44), (62, 84), (52, 140), (24, 172), (0, 186)], a, (120, 60, 170), 1)
    p.sym([(0, 50), (26, 58), (40, 90), (32, 132), (0, 160)], b, None)
    # The eye
    p.glow(p.cx, 94, 44, g)
    p.ellipse(p.cx, 94, 28, 19, (16, 8, 30), g)
    p.ellipse(p.cx, 94, 19, 15, g)
    p.ellipse(p.cx, 94, 5, 13, (20, 4, 26))
    p.circle(p.cx - 6, 88, 2.8, (255, 240, 255))
    return p.done(True)


BOSS_BUILDERS = {
    "warden": _boss_warden, "rockbreaker": _boss_rockbreaker, "crawler": _boss_crawler,
    "manta": _boss_manta, "scorpion": _boss_scorpion, "frost": _boss_frost,
    "stormlord": _boss_stormlord, "titan": _boss_titan, "hive": _boss_hive,
    "emperor": _boss_emperor,
}

# Pixel offsets of the core glow on each boss, for the pulse drawn during play
BOSS_CORE = {
    "warden": (0, 10, (120, 230, 255)), "rockbreaker": (0, -1, (255, 190, 70)),
    "crawler": (0, -2, (240, 230, 90)), "manta": (0, -1, (255, 170, 120)),
    "scorpion": (0, 27, (255, 90, 50)), "frost": (0, 0, (90, 240, 255)),
    "stormlord": (0, 0, (214, 130, 255)), "titan": (0, -1, (255, 130, 30)),
    "hive": (0, 0, (120, 255, 150)), "emperor": (0, 1, (255, 90, 220)),
}


class SpriteBook:
    """Builds sprites on first use and keeps them."""

    BUILDERS = {"scout": _scout, "fighter": _fighter, "bomber": _bomber, "saucer": _saucer,
                "interceptor": _interceptor, "drone": _drone}

    def __init__(self):
        self.cache = {}

    def _get(self, key, build):
        if key not in self.cache:
            self.cache[key] = build()
        return self.cache[key]

    def player(self):
        return self._get("player", player_ship)

    def enemy(self, kind, pal):
        return self._get((kind, pal), lambda: self.BUILDERS[kind](pal))

    def hull(self, pal):
        return self._get(("hull", pal), lambda: tank_hull(pal))

    def turret(self, pal):
        return self._get(("turret", pal), lambda: tank_turret(pal))

    def missile(self, pal):
        return self._get(("missile", pal), lambda: missile_sprite(pal))

    def asteroid(self, size, seed, tint):
        return self._get(("rock", size, seed, tint), lambda: asteroid_sprite(size, seed, tint))

    def boss(self, name):
        return self._get(("boss", name), BOSS_BUILDERS[name])


def flash_copy(sprite):
    """A pure white silhouette for the moment an enemy is hit."""
    mask = pygame.mask.from_surface(sprite, 40)
    return mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
