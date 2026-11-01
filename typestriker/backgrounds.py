"""One painted, scrolling backdrop per level. All drawn in code when a level loads."""
import math
import random

import pygame

from .art import additive, asteroid_sprite, dim, mix, radial, shade
from .config import WIDTH, HEIGHT

TILE_H = 1024


def _nebula(colors, blobs, seed, base=(4, 6, 16)):
    """Soft colour clouds that wrap vertically, painted small and scaled up."""
    rng = random.Random(seed)
    w, h = WIDTH // 4, TILE_H // 4
    low = pygame.Surface((w, h))
    low.fill(base)
    for _ in range(blobs):
        col = rng.choice(colors)
        col = shade(col, rng.uniform(0.25, 0.7))
        r = rng.randint(18, 70)
        glow = additive(r, col, 1.6)
        x, y = rng.randint(-r, w), rng.randint(0, h)
        for yy in (y - h, y, y + h):
            low.blit(glow, (x - r // 2, yy - r), special_flags=pygame.BLEND_RGB_ADD)
    return pygame.transform.smoothscale(low, (WIDTH, TILE_H))


def _noise_ground(colors, blobs, seed):
    """A mottled ground texture that wraps vertically."""
    rng = random.Random(seed)
    w, h = WIDTH // 4, TILE_H // 4
    low = pygame.Surface((w, h))
    low.fill(colors[0])
    for _ in range(blobs):
        col = rng.choice(colors)
        r = rng.randint(6, 34)
        glow = radial(r, col, 0.8)
        x, y = rng.randint(-r, w), rng.randint(0, h)
        for yy in (y - h, y, y + h):
            low.blit(glow, (x - r, yy - r))
    return pygame.transform.smoothscale(low, (WIDTH, TILE_H))


def _wrap_y(y, margin):
    """The y positions at which a feature must be drawn so that it tiles."""
    ys = [y]
    if y < margin:
        ys.append(y + TILE_H)
    if y > TILE_H - margin:
        ys.append(y - TILE_H)
    return ys


def _meander(seed_a, seed_b, x0, amp):
    """An x position for each y that lines up at the top and bottom of the tile."""
    def f(y):
        t = y / TILE_H * math.tau
        return x0 + amp * math.sin(t * seed_a) + amp * 0.45 * math.sin(t * seed_b + 1.2)
    return f


def _sphere(radius, base, seed, bands=False, land=None):
    """A lit planet with an atmosphere."""
    rng = random.Random(seed)
    size = radius * 2 + 80
    c = size // 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    disk = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(disk, (*base, 255), (c, c), radius)
    if bands:
        for _ in range(26):
            y = rng.randint(c - radius, c + radius)
            pygame.draw.rect(disk, (*shade(base, rng.uniform(0.7, 1.25)), 255),
                             (0, y, size, rng.randint(4, 22)))
    if land:
        for _ in range(26):
            r = rng.randint(radius // 12, radius // 5)
            a, d = rng.uniform(0, math.tau), rng.uniform(0, radius * 0.95)
            x, y = c + math.cos(a) * d, c + math.sin(a) * d
            for _ in range(9):
                pygame.draw.circle(disk, (*shade(land, rng.uniform(0.8, 1.15)), 255),
                                   (x + rng.randint(-r, r), y + rng.randint(-r // 2, r // 2)),
                                   rng.randint(max(2, r // 3), r // 2 + 2))
        for _ in range(50):
            x = rng.randint(c - radius, c + radius)
            y = rng.randint(c - radius, c + radius)
            pygame.draw.ellipse(disk, (250, 250, 255, 110), (x, y, rng.randint(14, 60), rng.randint(3, 9)))
    # Night side: a large dark glow pushed to the lower right
    fade = pygame.Surface((size, size), pygame.SRCALPHA)
    centre = (c + radius * 0.75, c + radius * 0.75)
    for i in range(48, -1, -1):
        t = i / 48
        pygame.draw.circle(fade, (0, 0, 8, int(235 * (1 - t) ** 1.3)), centre, int(radius * (0.65 + t * 1.25)))
    disk.blit(fade, (0, 0))
    # Keep the disk round
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (c, c), radius)
    disk.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    glow = radial(radius + 36, shade(mix(base, (180, 220, 255), 0.5), 0.9), 3.2)
    surf.blit(glow, (c - glow.get_width() // 2 - 6, c - glow.get_height() // 2 - 6))
    surf.blit(disk, (0, 0))
    return surf


def _rock_shape(rng, x, y, r, sq=0.7, n=11):
    return [(x + math.cos(i / n * math.tau) * r * rng.uniform(0.7, 1.15),
             y + math.sin(i / n * math.tau) * r * sq * rng.uniform(0.7, 1.15)) for i in range(n)]


# ---- Ground painters ------------------------------------------------------

def _paint_forest(seed):
    rng = random.Random(seed)
    tile = _noise_ground([(34, 82, 42), (28, 70, 40), (46, 98, 46), (60, 112, 50), (24, 60, 38)], 260, seed)
    river = _meander(1, 2, WIDTH * 0.62, 150)
    pts_l, pts_r = [], []
    for y in range(-20, TILE_H + 21, 8):
        width = 34 + 12 * math.sin(y / TILE_H * math.tau * 3)
        pts_l.append((river(y) - width, y))
        pts_r.append((river(y) + width, y))
    pygame.draw.polygon(tile, (168, 152, 96), [(x - 11, y) for x, y in pts_l] + [(x + 11, y) for x, y in reversed(pts_r)])
    pygame.draw.polygon(tile, (36, 104, 142), pts_l + list(reversed(pts_r)))
    inner = [(x + 13, y) for x, y in pts_l] + [(x - 13, y) for x, y in reversed(pts_r)]
    pygame.draw.polygon(tile, (54, 142, 176), inner)
    for _ in range(90):
        y = rng.randint(0, TILE_H)
        x = river(y) + rng.randint(-18, 18)
        pygame.draw.line(tile, (150, 214, 226), (x, y), (x + rng.randint(4, 14), y), 1)
    # Clearings
    for _ in range(5):
        x, y, r = rng.randint(40, WIDTH - 40), rng.randint(0, TILE_H), rng.randint(40, 80)
        for yy in _wrap_y(y, 110):
            pygame.draw.polygon(tile, (112, 142, 66), _rock_shape(rng, x, yy, r, 0.7))
    # Trees, far ones first; none in the river
    trees = []
    for _ in range(1100):
        x, y = rng.randint(0, WIDTH), rng.randint(0, TILE_H)
        if abs(x - river(y)) < 62:
            continue
        trees.append((y, x, rng.randint(6, 13), rng.choice(((24, 88, 44), (32, 104, 48), (20, 76, 44), (46, 118, 50)))))
    trees.sort()
    for y, x, r, col in trees:
        for yy in _wrap_y(y, 20):
            pygame.draw.circle(tile, (12, 40, 26), (x + 3, yy + 4), r)
            pygame.draw.circle(tile, col, (x, yy), r)
            pygame.draw.circle(tile, shade(col, 1.35), (x - r // 3, yy - r // 3), r // 2)
    return tile


def _paint_desert(seed):
    rng = random.Random(seed)
    tile = _noise_ground([(202, 158, 96), (214, 172, 106), (188, 142, 84), (224, 186, 122)], 240, seed)
    # Wind ripples in long arcs
    for _ in range(170):
        x, y = rng.randint(-60, WIDTH), rng.randint(0, TILE_H)
        w = rng.randint(70, 240)
        h = rng.randint(14, 42)
        col = shade((206, 162, 98), rng.choice((0.8, 0.86, 1.1, 1.16)))
        for yy in _wrap_y(y, 60):
            pygame.draw.arc(tile, col, (x, yy, w, h), 0.2, math.pi - 0.2, rng.randint(2, 4))
    # Craters
    for _ in range(14):
        x, y, r = rng.randint(30, WIDTH - 30), rng.randint(0, TILE_H), rng.randint(12, 34)
        for yy in _wrap_y(y, 50):
            pygame.draw.ellipse(tile, (232, 196, 136), (x - r, yy - r * 0.7, r * 2 + 3, r * 1.4 + 3))
            pygame.draw.ellipse(tile, (154, 114, 70), (x - r, yy - r * 0.7, r * 2, r * 1.4))
            pygame.draw.ellipse(tile, (178, 136, 84), (x - r * 0.7, yy - r * 0.3, r * 1.5, r * 0.95))
    # Mesas: dark shadow, cliff, sunlit layered top
    for _ in range(16):
        x, y, r = rng.randint(0, WIDTH), rng.randint(0, TILE_H), rng.randint(34, 86)
        shape = _rock_shape(rng, 0, 0, r, 0.72)
        for yy in _wrap_y(y, 140):
            pygame.draw.polygon(tile, (92, 58, 38), [(x + a + 13, yy + b + 16) for a, b in shape])
            pygame.draw.polygon(tile, (152, 88, 52), [(x + a, yy + b + 9) for a, b in shape])
            pygame.draw.polygon(tile, (206, 128, 72), [(x + a, yy + b) for a, b in shape])
            pygame.draw.polygon(tile, (230, 158, 96), [(x + a * 0.68 - 3, yy + b * 0.68 - 3) for a, b in shape])
            pygame.draw.polygon(tile, (242, 186, 124), [(x + a * 0.34 - 5, yy + b * 0.34 - 5) for a, b in shape])
    return tile


def _paint_ice(seed):
    rng = random.Random(seed)
    tile = _noise_ground([(204, 228, 244), (222, 240, 250), (180, 212, 236), (238, 248, 254)], 240, seed)
    # Frozen lakes
    for _ in range(9):
        x, y, r = rng.randint(30, WIDTH - 30), rng.randint(0, TILE_H), rng.randint(50, 120)
        shape = _rock_shape(rng, 0, 0, r, 0.75, 14)
        for yy in _wrap_y(y, 170):
            pygame.draw.polygon(tile, (246, 252, 255), [(x + a * 1.08, yy + b * 1.08) for a, b in shape])
            pygame.draw.polygon(tile, (106, 172, 216), [(x + a, yy + b) for a, b in shape])
            pygame.draw.polygon(tile, (138, 200, 232), [(x + a * 0.72 - 6, yy + b * 0.72 - 5) for a, b in shape])
            pygame.draw.line(tile, (226, 246, 255), (x - r * 0.4, yy - r * 0.2), (x + r * 0.1, yy - r * 0.3), 2)
    # Crevasses: jagged dark cracks with a bright lip
    for _ in range(26):
        x, y = rng.randint(0, WIDTH), rng.randint(0, TILE_H)
        pts = [(x, y)]
        ang = rng.uniform(0, math.tau)
        for _ in range(rng.randint(4, 10)):
            ang += rng.uniform(-0.7, 0.7)
            x += math.cos(ang) * rng.randint(16, 40)
            y += math.sin(ang) * rng.randint(16, 40)
            pts.append((x, y))
        for dy in (0, -TILE_H, TILE_H):
            shifted = [(a, b + dy) for a, b in pts]
            pygame.draw.lines(tile, (250, 253, 255), False, [(a + 2, b + 2) for a, b in shifted], 3)
            pygame.draw.lines(tile, (66, 112, 164), False, shifted, rng.randint(2, 4))
    # Ice boulders
    for _ in range(46):
        x, y, r = rng.randint(0, WIDTH), rng.randint(0, TILE_H), rng.randint(7, 22)
        shape = _rock_shape(rng, 0, 0, r, 0.8, 7)
        for yy in _wrap_y(y, 40):
            pygame.draw.polygon(tile, (120, 156, 196), [(x + a + 5, yy + b + 6) for a, b in shape])
            pygame.draw.polygon(tile, (172, 214, 238), [(x + a, yy + b) for a, b in shape])
            pygame.draw.polygon(tile, (250, 254, 255), [(x + a * 0.55 - 2, yy + b * 0.55 - 3) for a, b in shape])
    return tile


def _paint_lava(seed):
    rng = random.Random(seed)
    tile = _noise_ground([(36, 26, 26), (46, 32, 30), (28, 22, 24), (58, 40, 34)], 260, seed)
    # Lava rivers: wide glow, orange body, yellow core
    for x0, amp, a, b, width in ((WIDTH * 0.26, 120, 1, 3, 26), (WIDTH * 0.76, 90, 2, 1, 20)):
        river = _meander(a, b, x0, amp)
        for w, col in ((width + 22, (96, 26, 8)), (width + 12, (176, 50, 8)), (width + 5, (240, 92, 14)),
                       (width - 2, (255, 150, 30)), (width // 2, (255, 214, 90))):
            pts_l, pts_r = [], []
            for y in range(-20, TILE_H + 21, 8):
                k = 1 + 0.3 * math.sin(y / TILE_H * math.tau * 4 + x0)
                pts_l.append((river(y) - w * k, y))
                pts_r.append((river(y) + w * k, y))
            pygame.draw.polygon(tile, col, pts_l + list(reversed(pts_r)))
    # Glowing cracks
    for _ in range(36):
        x, y = rng.randint(0, WIDTH), rng.randint(0, TILE_H)
        pts = [(x, y)]
        ang = rng.uniform(0, math.tau)
        for _ in range(rng.randint(3, 8)):
            ang += rng.uniform(-0.8, 0.8)
            x += math.cos(ang) * rng.randint(10, 30)
            y += math.sin(ang) * rng.randint(10, 30)
            pts.append((x, y))
        for dy in (0, -TILE_H, TILE_H):
            shifted = [(a, b + dy) for a, b in pts]
            pygame.draw.lines(tile, (170, 50, 10), False, shifted, 4)
            pygame.draw.lines(tile, (255, 150, 40), False, shifted, 1)
    # Black basalt islands
    for _ in range(48):
        x, y, r = rng.randint(0, WIDTH), rng.randint(0, TILE_H), rng.randint(10, 52)
        shape = _rock_shape(rng, 0, 0, r, 0.8)
        for yy in _wrap_y(y, 80):
            pygame.draw.polygon(tile, (14, 10, 14), [(x + a + 5, yy + b + 7) for a, b in shape])
            pygame.draw.polygon(tile, (54, 42, 42), [(x + a, yy + b) for a, b in shape])
            pygame.draw.polygon(tile, (78, 62, 58), [(x + a * 0.62 - 3, yy + b * 0.62 - 3) for a, b in shape])
    return tile


def _paint_hull(seed):
    rng = random.Random(seed)
    tile = pygame.Surface((WIDTH, TILE_H))
    tile.fill((44, 42, 62))
    size = 64
    for gy in range(0, TILE_H, size):
        for gx in range(0, WIDTH, size):
            f = rng.uniform(0.82, 1.2)
            col = shade((64, 60, 88), f)
            r = pygame.Rect(gx + 1, gy + 1, size - 2, size - 2)
            pygame.draw.rect(tile, col, r)
            pygame.draw.line(tile, shade(col, 1.3), r.topleft, r.topright)
            pygame.draw.line(tile, shade(col, 1.3), r.topleft, r.bottomleft)
            pygame.draw.line(tile, shade(col, 0.6), r.bottomleft, r.bottomright)
            pygame.draw.line(tile, shade(col, 0.6), r.topright, r.bottomright)
            for cx, cy in (r.topleft, r.topright, r.bottomleft, r.bottomright):
                pygame.draw.circle(tile, shade(col, 0.55), (cx + (4 if cx == r.left else -4), cy + (4 if cy == r.top else -4)), 1)
    # Large plates raised off the hull
    for _ in range(20):
        w, h = rng.randrange(128, 320, 64), rng.randrange(128, 320, 64)
        x, y = rng.randrange(0, WIDTH, 64), rng.randrange(0, TILE_H, 64)
        col = shade((82, 76, 112), rng.uniform(0.85, 1.15))
        for yy in _wrap_y(y, h + 20) + ([y - TILE_H] if y + h > TILE_H else []):
            pygame.draw.rect(tile, (20, 18, 32), (x + 7, yy + 9, w, h), border_radius=6)
            pygame.draw.rect(tile, col, (x, yy, w, h), border_radius=6)
            pygame.draw.rect(tile, shade(col, 1.3), (x, yy, w, h), 2, border_radius=6)
            pygame.draw.rect(tile, shade(col, 0.82), (x + 14, yy + 14, w - 28, h - 28), 2, border_radius=4)
    # Two long trenches with green light strips
    for x in (WIDTH // 4 - 30, 3 * WIDTH // 4 - 30):
        pygame.draw.rect(tile, (12, 12, 22), (x, 0, 60, TILE_H))
        pygame.draw.rect(tile, (30, 28, 46), (x + 4, 0, 52, TILE_H))
        pygame.draw.line(tile, (110, 104, 148), (x, 0), (x, TILE_H), 2)
        pygame.draw.line(tile, (110, 104, 148), (x + 60, 0), (x + 60, TILE_H), 2)
        pygame.draw.rect(tile, (60, 200, 110), (x + 27, 0, 6, TILE_H))
        pygame.draw.rect(tile, (190, 255, 210), (x + 29, 0, 2, TILE_H))
        for y in range(0, TILE_H, 32):
            pygame.draw.line(tile, (56, 52, 80), (x + 4, y), (x + 56, y), 2)
    # Vents
    for _ in range(14):
        x, y = rng.randrange(0, WIDTH - 90, 32), rng.randrange(0, TILE_H - 50, 32)
        pygame.draw.rect(tile, (18, 18, 30), (x, y, 80, 40), border_radius=4)
        for i in range(5):
            pygame.draw.rect(tile, (86, 82, 116), (x + 6, y + 5 + i * 7, 68, 3))
    return tile


PAINTERS = {"forest": _paint_forest, "desert": _paint_desert, "ice": _paint_ice,
            "lava": _paint_lava, "hull": _paint_hull}


def _make_cloud(seed, colors, width=340, height=170, puffs=26):
    rng = random.Random(seed)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for _ in range(puffs):
        r = rng.randint(24, 58)
        x = rng.randint(r, width - r)
        y = height // 2 + rng.randint(-height // 4, height // 4)
        puff = radial(r, rng.choice(colors), 1.4)
        surf.blit(puff, (x - r, y - r))
    return surf


class Background:
    """Scrolling backdrop for one level. `scroll_speed` matches the ground units."""

    def __init__(self, theme, scroll_speed=70, seed=1):
        self.theme = theme
        self.rng = random.Random(seed)
        self.scroll_speed = scroll_speed
        self.y = 0.0
        self.time = 0.0
        self.flash = 0.0
        self.bolt = None
        self.bolt_time = 0.0
        self.next_bolt = 2.5
        self.props = []
        self.embers = []
        self.lights = []
        self.clouds = []
        self.stars = []
        self.ground = theme in PAINTERS
        self.tile = (PAINTERS[theme](seed) if self.ground else self._space_tile()).convert()
        self._prepare()

    # ---- set-up ---------------------------------------------------------
    def _space_tile(self):
        return {
            "orbit": lambda: _nebula([(30, 60, 150), (50, 90, 190), (70, 40, 140)], 60, 3),
            "belt": lambda: _nebula([(120, 70, 30), (150, 96, 44), (80, 44, 40)], 70, 5, (10, 7, 8)),
            "nebula": lambda: _nebula([(190, 30, 70), (130, 20, 110), (230, 80, 70), (60, 20, 100)],
                                      110, 7, (14, 3, 14)),
            "storm": lambda: _nebula([(20, 120, 130), (60, 40, 150), (30, 70, 170)], 90, 9, (3, 8, 18)),
            "blackhole": lambda: _nebula([(50, 16, 70), (90, 24, 70), (20, 16, 60)], 60, 11, (2, 1, 6)),
        }[self.theme]()

    def _prepare(self):
        rng = self.rng
        if not self.ground:
            palette = {"orbit": [(255, 255, 255), (190, 215, 255)],
                       "belt": [(255, 240, 215), (255, 210, 170)],
                       "nebula": [(255, 225, 225), (255, 180, 200)],
                       "storm": [(205, 255, 250), (220, 200, 255)],
                       "blackhole": [(255, 225, 255), (215, 180, 255)]}[self.theme]
            for _ in range(170):
                depth = rng.random()
                self.stars.append([rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), depth,
                                   rng.choice(palette), rng.uniform(0, 6.28)])
        if self.theme == "orbit":
            self.props.append(self._prop(_sphere(250, (36, 96, 176), 21, land=(62, 138, 74)), 700, 300, 7))
            self.props.append(self._prop(_sphere(26, (190, 190, 200), 9), 120, -40, 11))
        elif self.theme == "belt":
            self.props.append(self._prop(self._ringed_giant(), 200, 120, 5))
            for layer, (count, speed, tone) in enumerate(((16, 22, 0.26), (10, 44, 0.42))):
                for i in range(count):
                    size = rng.randint(30, 90) + layer * 22
                    sprite = asteroid_sprite(size, 40 + layer * 50 + i, shade((150, 118, 92), tone * 2.2))
                    self.props.append(self._prop(sprite, rng.randint(0, WIDTH), rng.randint(-200, HEIGHT), speed))
        elif self.theme == "nebula":
            for _ in range(3):
                self.props.append(self._prop(radial(rng.randint(90, 170), (255, 180, 170), 2.4),
                                             rng.randint(0, WIDTH), rng.randint(0, HEIGHT), rng.randint(10, 18)))
        elif self.theme == "storm":
            self.props.append(self._prop(_sphere(120, (44, 66, 122), 14, bands=True), 180, 120, 6))
        elif self.theme == "blackhole":
            self.disk = self._accretion_disk()
            self.halo = additive(112, (255, 196, 130), 2.2)
            self.front = self._disk_front()
            self.orbiters = [[rng.uniform(0, 6.28), rng.uniform(150, 440), rng.uniform(0.2, 0.9),
                              rng.choice(((255, 180, 90), (255, 110, 220), (190, 140, 255)))]
                             for _ in range(90)]
        elif self.theme == "forest":
            self.clouds = self._cloud_set([(255, 255, 255), (235, 245, 245)], 90)
        elif self.theme == "desert":
            self.clouds = self._cloud_set([(240, 206, 150), (226, 186, 124)], 60)
        elif self.theme == "ice":
            self.clouds = self._cloud_set([(255, 255, 255), (230, 242, 255)], 110)
            self.embers = [[rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), rng.uniform(50, 130), rng.uniform(1, 2.4)]
                           for _ in range(70)]
        elif self.theme == "lava":
            self.clouds = self._cloud_set([(46, 36, 40), (70, 46, 40)], 120)
            self.embers = [[rng.uniform(0, WIDTH), rng.uniform(0, HEIGHT), rng.uniform(40, 140), rng.uniform(1, 2.6)]
                           for _ in range(60)]
        elif self.theme == "hull":
            for _ in range(36):
                self.lights.append((rng.randrange(0, WIDTH, 64) + 6, rng.randrange(0, TILE_H, 64) + 6,
                                    rng.uniform(0, 6.28), rng.choice(((255, 80, 80), (120, 255, 150), (120, 200, 255)))))

    def _prop(self, surface, x, y, speed):
        return [surface, float(x), float(y), speed]

    def _cloud_set(self, colors, alpha):
        out = []
        for i in range(6):
            cloud = _make_cloud(30 + i, colors)
            cloud.set_alpha(alpha)
            shadow = cloud.copy()
            shadow.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
            shadow.set_alpha(alpha // 3)
            out.append([cloud, shadow, self.rng.uniform(-100, WIDTH - 200), self.rng.uniform(-200, HEIGHT)])
        return out

    def _ringed_giant(self):
        planet = _sphere(120, (196, 142, 88), 17, bands=True)
        w, h = planet.get_size()
        surf = pygame.Surface((w + 260, h + 40), pygame.SRCALPHA)
        big = pygame.Surface(((w + 260) * 3, 330), pygame.SRCALPHA)
        for i, col in enumerate(((220, 190, 140, 170), (180, 150, 110, 120), (230, 210, 170, 150))):
            pygame.draw.ellipse(big, col, (18 + i * 66, 6 + i * 21, (w + 248 - i * 44) * 3, (106 - i * 14) * 3), 27)
        rings = pygame.transform.smoothscale(big, (w + 260, 110))
        rings = pygame.transform.rotozoom(rings, 14, 1.0)
        cx, cy = surf.get_width() // 2, surf.get_height() // 2
        surf.blit(rings, (cx - rings.get_width() // 2, cy - rings.get_height() // 2))
        front = surf.copy()
        surf.blit(planet, (cx - w // 2, cy - h // 2))
        # The near half of the rings passes in front of the planet
        surf.blit(front, (0, cy + 12), (0, cy + 12, surf.get_width(), surf.get_height()))
        return surf

    def _disk_front(self):
        """A flat streak of light: the near edge of the disk, in front of the hole."""
        low = pygame.Surface((256, 16))
        for x in range(256):
            for y in range(16):
                k = (1 - abs(x - 127.5) / 128) ** 0.8 * (1 - abs(y - 7.5) / 8) ** 1.6
                low.set_at((x, y), shade((255, 214, 160), k))
        return pygame.transform.smoothscale(low, (640, 34))

    def _accretion_disk(self):
        w, h = 760, 300
        surf = pygame.Surface((w, h))
        cx, cy = w // 2, h // 2
        for i in range(60, 0, -1):
            t = i / 60
            col = mix((255, 240, 190), (120, 10, 110), t ** 0.7)
            col = shade(col, (1 - t) ** 0.7)
            rect = pygame.Rect(0, 0, int(w * t), int(h * t))
            rect.center = (cx, cy)
            pygame.draw.ellipse(surf, col, rect)
        return surf

    # ---- per frame ------------------------------------------------------
    def update(self, dt):
        self.time += dt
        self.y = (self.y + self.scroll_speed * dt * (1.0 if self.ground else 0.35)) % TILE_H
        self.flash = max(0.0, self.flash - dt * 3.2)
        if self.theme == "storm":
            self.bolt_time -= dt
            self.next_bolt -= dt
            if self.next_bolt <= 0:
                self.next_bolt = self.rng.uniform(1.6, 4.5)
                self.flash = 1.0
                self.bolt_time = 0.22
                self.bolt = self._bolt_points()
        for prop in self.props:
            prop[2] += prop[3] * dt
            if prop[2] > HEIGHT + 40:
                prop[2] = -prop[0].get_height() - self.rng.randint(0, 200)
                prop[1] = self.rng.randint(-40, WIDTH - 40)
        for star in self.stars:
            star[1] += (14 + star[2] * star[2] * 150) * dt
            if star[1] > HEIGHT:
                star[1] = 0
                star[0] = self.rng.uniform(0, WIDTH)
        for ember in self.embers:
            if self.theme == "ice":
                ember[1] += ember[2] * dt
                ember[0] += math.sin(self.time + ember[2]) * 18 * dt
                if ember[1] > HEIGHT:
                    ember[1] = -4
            else:
                ember[1] -= ember[2] * dt
                ember[0] += math.sin(self.time * 2 + ember[2]) * 22 * dt
                if ember[1] < -4:
                    ember[1] = HEIGHT + 4
                    ember[0] = self.rng.uniform(0, WIDTH)
        for cloud in self.clouds:
            cloud[3] += self.scroll_speed * 1.7 * dt
            if cloud[3] > HEIGHT + 60:
                cloud[3] = -self.rng.uniform(200, 420)
                cloud[2] = self.rng.uniform(-120, WIDTH - 200)

    def _bolt_points(self):
        rng = self.rng
        x, y = rng.uniform(60, WIDTH - 60), 0
        pts = [(x, y)]
        while y < HEIGHT * rng.uniform(0.6, 1.0):
            x += rng.uniform(-60, 60)
            y += rng.uniform(26, 70)
            pts.append((x, y))
        return pts

    def draw(self, surf):
        y = int(self.y)
        surf.blit(self.tile, (0, y - TILE_H))
        surf.blit(self.tile, (0, y))
        if self.theme == "blackhole":
            self._draw_blackhole(surf)
        self._draw_stars(surf)
        for prop in self.props:
            surf.blit(prop[0], (prop[1], prop[2]))
        if self.theme == "hull":
            self._draw_lights(surf, y)
        if self.clouds:
            for cloud, shadow, cx, cy in self.clouds:
                surf.blit(shadow, (cx + 46, cy + 66))
            for cloud, shadow, cx, cy in self.clouds:
                surf.blit(cloud, (cx, cy))
        self._draw_particles(surf)
        if self.theme == "storm":
            self._draw_storm(surf)

    def _draw_stars(self, surf):
        for x, y, depth, col, phase in self.stars:
            twinkle = 0.65 + 0.35 * math.sin(self.time * (1 + depth * 3) + phase)
            bright = shade(col, (0.3 + depth * 0.7) * twinkle)
            if depth > 0.86:
                length = 2 + int(depth * 7)
                surf.fill(bright, (x, y, 2, length))
                surf.fill(shade(bright, 0.4), (x - 1, y + 1, 4, 1))
            elif depth > 0.5:
                surf.fill(bright, (x, y, 2, 2))
            else:
                surf.fill(bright, (x, y, 1, 1))

    def _draw_lights(self, surf, y):
        for lx, ly, phase, col in self.lights:
            k = 0.5 + 0.5 * math.sin(self.time * 3 + phase)
            py = (ly + y) % TILE_H
            if py < HEIGHT + 20:
                g = additive(11, dim(col, k), 1.4)
                surf.blit(g, (lx - 11, py - 11), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_particles(self, surf):
        if self.theme == "lava":
            for x, y, speed, size in self.embers:
                g = additive(int(size * 2.4), (255, 130, 40), 1.4)
                surf.blit(g, (x, y), special_flags=pygame.BLEND_RGB_ADD)
        elif self.theme == "ice":
            for x, y, speed, size in self.embers:
                pygame.draw.circle(surf, (250, 253, 255), (x, y), size)

    def _draw_storm(self, surf):
        if self.bolt_time > 0 and self.bolt:
            pygame.draw.lines(surf, (130, 110, 255), False, self.bolt, 7)
            pygame.draw.lines(surf, (210, 200, 255), False, self.bolt, 3)
            pygame.draw.lines(surf, (255, 255, 255), False, self.bolt, 1)
        if self.flash > 0:
            v = int(46 * self.flash)
            surf.fill((v // 2, v // 2, v), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_blackhole(self, surf):
        cx, cy = WIDTH // 2, 300
        surf.blit(self.disk, (cx - 380, cy - 150), special_flags=pygame.BLEND_RGB_ADD)
        for orb in self.orbiters:
            orb[0] += orb[2] * 0.016 * (260 / orb[1]) * 3
            orb[1] -= 0.09
            if orb[1] < 80:
                orb[1] = self.rng.uniform(380, 460)
            x = cx + math.cos(orb[0]) * orb[1]
            y = cy + math.sin(orb[0]) * orb[1] * 0.38
            if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                g = additive(5, orb[3], 1.4)
                surf.blit(g, (x - 5, y - 5), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self.halo, (cx - self.halo.get_width() // 2, cy - self.halo.get_height() // 2),
                  special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.circle(surf, (0, 0, 0), (cx, cy), 74)
        # The bright front of the disk sweeps across the hole
        surf.blit(self.front, (cx - self.front.get_width() // 2, cy + 4 - self.front.get_height() // 2),
                  special_flags=pygame.BLEND_RGB_ADD)

