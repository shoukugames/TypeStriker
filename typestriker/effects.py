"""Particles, shockwaves, floating text and the explosion recipes."""
import math
import random

import pygame

from .art import additive, dim, shade

BLOWUP = {
    # colours, particle count, speed, debris colour, ring size
    "scout": ((255, 230, 120), 22, 190, None, 44),
    "fighter": ((255, 150, 60), 34, 210, None, 62),
    "bomber": ((255, 110, 50), 56, 240, None, 96),
    "saucer": ((160, 240, 255), 40, 220, None, 74),
    "interceptor": ((240, 190, 255), 26, 280, None, 54),
    "drone": ((150, 255, 170), 28, 200, None, 56),
    "tank": ((255, 170, 60), 50, 180, (40, 40, 44), 84),
    "asteroid": ((255, 214, 170), 14, 120, (120, 100, 84), 40),
    "missile": ((255, 255, 210), 24, 330, None, 40),
}


class Effects:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.particles = []  # x, y, vx, vy, life, max_life, radius, color, drag, additive
        self.rings = []      # x, y, radius, speed, life, max_life, color
        self.popups = []     # x, y, text surface, life
        self.decals = []     # x, y, surface: scorch marks that scroll with the ground
        self.shake = 0.0

    def spark(self, x, y, color, count=8, speed=160, life=0.35, radius=4):
        for _ in range(count):
            a = self.rng.uniform(0, math.tau)
            s = self.rng.uniform(0.3, 1.0) * speed
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s,
                                   self.rng.uniform(0.5, 1.0) * life, life, radius, color, 3.0, True])

    def trail(self, x, y, color, radius=4, life=0.35):
        self.particles.append([x + self.rng.uniform(-2, 2), y + self.rng.uniform(-2, 2),
                               self.rng.uniform(-14, 14), self.rng.uniform(-14, 14),
                               life, life, radius, color, 1.0, True])

    def smoke(self, x, y, count=6, color=(70, 70, 76)):
        for _ in range(count):
            a = self.rng.uniform(0, math.tau)
            s = self.rng.uniform(10, 60)
            life = self.rng.uniform(0.5, 1.1)
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s, life, life,
                                   self.rng.uniform(7, 15), color, 1.5, False])

    def debris(self, x, y, color, count=10, speed=200):
        for _ in range(count):
            a = self.rng.uniform(0, math.tau)
            s = self.rng.uniform(0.3, 1.0) * speed
            life = self.rng.uniform(0.4, 0.95)
            self.particles.append([x, y, math.cos(a) * s, math.sin(a) * s, life, life,
                                   self.rng.uniform(2.0, 5.0), color, 1.2, False])

    def ring(self, x, y, size, color=(255, 240, 200), life=0.35):
        self.rings.append([x, y, 6.0, size / life, life, life, color])

    def explode(self, kind, x, y, tint=None):
        color, count, speed, debris, ring = BLOWUP.get(kind, BLOWUP["fighter"])
        self.spark(x, y, color, count, speed, 0.55, 7)
        self.spark(x, y, (255, 255, 240), count // 3, speed * 0.5, 0.3, 9)
        self.ring(x, y, ring, shade(color, 1.1))
        self.debris(x, y, debris or tint or (130, 130, 150), 12, speed * 0.9)
        if kind in ("tank", "bomber", "asteroid"):
            self.smoke(x, y, 10, (60, 56, 58) if kind != "asteroid" else (120, 100, 84))
        if kind == "tank":
            scorch = pygame.Surface((90, 90), pygame.SRCALPHA)
            for i in range(14):
                r = 36 - i * 2
                pygame.draw.circle(scorch, (14, 12, 12, 16 + i * 8), (45, 45), r)
            self.decals.append([x - 45, y - 45, scorch])
        self.shake = max(self.shake, 7 if kind in ("bomber", "tank") else 4)

    def big_blast(self, x, y, color):
        self.spark(x, y, color, 60, 380, 0.9, 11)
        self.spark(x, y, (255, 255, 240), 30, 200, 0.6, 14)
        self.ring(x, y, 170, color, 0.5)
        self.debris(x, y, (70, 70, 84), 22, 300)
        self.shake = max(self.shake, 12)

    def popup(self, x, y, text_surface, life=0.8):
        self.popups.append([x, y, text_surface, life, life])

    def update(self, dt, ground_speed=0.0):
        keep = []
        for p in self.particles:
            p[4] -= dt
            if p[4] > 0:
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                drag = max(0.0, 1.0 - p[8] * dt)
                p[2] *= drag
                p[3] *= drag
                keep.append(p)
        self.particles = keep[-650:]
        for r in self.rings:
            r[4] -= dt
            r[2] += r[3] * dt
        self.rings = [r for r in self.rings if r[4] > 0]
        for t in self.popups:
            t[3] -= dt
            t[1] -= 52 * dt
        self.popups = [t for t in self.popups if t[3] > 0]
        for d in self.decals:
            d[1] += ground_speed * dt
        self.decals = [d for d in self.decals if d[1] < 760]
        self.shake = max(0.0, self.shake - 34 * dt)

    def shake_offset(self):
        if self.shake <= 0:
            return 0, 0
        return (self.rng.uniform(-self.shake, self.shake), self.rng.uniform(-self.shake, self.shake))

    def draw_decals(self, surf):
        for x, y, s in self.decals:
            surf.blit(s, (x, y))

    def draw(self, surf):
        for p in self.particles:
            k = p[4] / p[5]
            if p[9]:
                r = max(1, int(p[6] * (0.4 + k * 0.8)))
                g = additive(r * 2, dim(p[7], 0.25 + 0.75 * k), 1.5)
                surf.blit(g, (p[0] - g.get_width() / 2, p[1] - g.get_height() / 2),
                          special_flags=pygame.BLEND_RGB_ADD)
            else:
                r = max(1, int(p[6] * (0.6 + k * 0.5)))
                pygame.draw.circle(surf, shade(p[7], 0.6 + 0.4 * k), (p[0], p[1]), r)
        for x, y, r, _, life, max_life, col in self.rings:
            k = life / max_life
            width = max(1, int(5 * k))
            pygame.draw.circle(surf, shade(col, 0.4 + 0.6 * k), (x, y), int(r), width)
        for x, y, text, life, max_life in self.popups:
            text.set_alpha(int(255 * min(1.0, life / max_life * 2)))
            surf.blit(text, (x - text.get_width() / 2, y - text.get_height() / 2))
