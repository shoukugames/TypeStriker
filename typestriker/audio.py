"""All sound is synthesised in code: effects, instruments and the music sequencer.

Nothing here needs a sound file. If no audio device exists the game carries on
silently, because every public method checks `self.enabled`.
"""
import array
import math
import random

import pygame

from .config import MENU_THEME

SAMPLE_RATE = 22050
MUSIC_CHANNELS = 5
TWO_PI = 2 * math.pi


def _osc(wave, phase):
    p = phase % 1.0
    if wave == "sine":
        return math.sin(TWO_PI * p)
    if wave == "square":
        return 1.0 if p < 0.5 else -1.0
    if wave == "saw":
        return 2.0 * p - 1.0
    return 4.0 * abs(p - 0.5) - 1.0  # triangle


def _voice(dur, f0, f1=None, wave="sine", vol=0.5, curve=4.0, attack=0.002, vibrato=(0, 0)):
    """A pitch sweep from f0 to f1 with an exponential decay."""
    n = int(dur * SAMPLE_RATE)
    f1 = f0 if f1 is None else f1
    out = [0.0] * n
    phase = 0.0
    vib_rate, vib_depth = vibrato
    attack_n = max(1, int(attack * SAMPLE_RATE))
    for i in range(n):
        t = i / n
        freq = f0 * (f1 / f0) ** t
        if vib_depth:
            freq *= 1.0 + vib_depth * math.sin(TWO_PI * vib_rate * i / SAMPLE_RATE)
        phase += freq / SAMPLE_RATE
        env = math.exp(-curve * t) * min(1.0, i / attack_n) * (1.0 - t * t * t)
        out[i] = _osc(wave, phase) * env * vol
    return out


def _noise(dur, vol=0.5, cutoff=0.5, cutoff_end=None, curve=4.0, seed=1):
    """Filtered noise. The cutoff (0..1) can glide, which gives a falling boom."""
    rng = random.Random(seed)
    n = int(dur * SAMPLE_RATE)
    out = [0.0] * n
    last = 0.0
    end = cutoff if cutoff_end is None else cutoff_end
    for i in range(n):
        t = i / n
        a = cutoff + (end - cutoff) * t
        last += a * (rng.uniform(-1, 1) - last)
        out[i] = last * math.exp(-curve * t) * (1.0 - t * t * t) * vol
    return out


def _mix(*parts):
    n = max(len(p) for p in parts)
    out = [0.0] * n
    for part in parts:
        for i, v in enumerate(part):
            out[i] += v
    return out


def _seq(*parts):
    out = []
    for part in parts:
        out.extend(part)
    return out


def _delay(part, seconds):
    return [0.0] * int(seconds * SAMPLE_RATE) + part


def _sound(samples):
    data = array.array("h", (int(max(-1.0, min(1.0, s)) * 32000) for s in samples))
    return pygame.mixer.Sound(buffer=data.tobytes())


def _build_effects():
    v, nz = _voice, _noise
    return {
        # Player
        "laser": v(0.09, 1500, 500, "square", 0.16, 3),
        "charge_shot": _mix(v(0.28, 300, 1600, "saw", 0.26, 2), nz(0.28, 0.2, 0.6, curve=3)),
        "lock": v(0.05, 980, 1200, "sine", 0.22, 2),
        "wrong": v(0.11, 150, 120, "square", 0.16, 2),
        "player_hit": _mix(nz(0.3, 0.7, 0.6, 0.1, 4), v(0.3, 240, 60, "saw", 0.4, 3)),
        "life_lost": _mix(nz(0.9, 0.8, 0.5, 0.03, 3), v(0.9, 500, 40, "saw", 0.4, 2)),
        # A different sound for each kind of enemy or object destroyed
        "destroy_scout": _mix(v(0.22, 420, 1700, "square", 0.3, 4), nz(0.12, 0.3, 0.8)),
        "destroy_fighter": _mix(v(0.36, 760, 110, "saw", 0.35, 3), nz(0.36, 0.5, 0.5, 0.08)),
        "destroy_bomber": _mix(v(0.65, 140, 34, "square", 0.42, 3), nz(0.65, 0.8, 0.35, 0.03, 3)),
        "destroy_saucer": _mix(v(0.48, 950, 240, "sine", 0.5, 2, vibrato=(26, 0.2)),
                               nz(0.2, 0.2, 0.5)),
        "destroy_interceptor": _seq(v(0.08, 1500, 1000, "square", 0.3, 2),
                                    _mix(v(0.16, 1000, 400, "square", 0.3, 3), nz(0.16, 0.35, 0.7))),
        "destroy_drone": _seq(*[v(0.035, f, None, "square", 0.26, 1)
                                for f in (1300, 760, 1100, 540, 900, 320, 640, 180)]),
        "destroy_tank": _mix(v(0.55, 220, 190, "triangle", 0.3, 5),
                             v(0.55, 347, 320, "square", 0.12, 7),
                             v(0.45, 513, 490, "square", 0.09, 9),
                             nz(0.6, 0.9, 0.3, 0.02, 3)),
        "destroy_asteroid": _mix(nz(0.2, 0.9, 0.22, 0.05, 3, seed=2),
                                 _delay(nz(0.2, 0.7, 0.2, 0.04, 3, seed=3), 0.07),
                                 _delay(nz(0.25, 0.5, 0.14, 0.03, 3, seed=4), 0.15)),
        "destroy_missile": _mix(nz(0.16, 0.8, 0.98, 0.3, 5, seed=5),
                                v(0.2, 2300, 280, "saw", 0.26, 3)),
        # Bosses
        "boss_warning": _seq(*[v(0.28, f, g, "square", 0.24, 0.6)
                               for f, g in ((440, 660), (660, 440), (440, 660), (660, 440))]),
        "boss_hit": _mix(v(0.25, 200, 70, "square", 0.4, 3), nz(0.25, 0.6, 0.6, 0.1)),
        "boss_explode": _mix(nz(1.8, 0.8, 0.5, 0.02, 2.5), v(1.8, 170, 22, "saw", 0.4, 2),
                             _delay(nz(0.7, 0.7, 0.4, 0.05, 3, seed=8), 0.35)),
        "enemy_shot": v(0.08, 620, 300, "triangle", 0.11, 3),
        # Jingles
        "level_clear": _seq(*[v(0.13, f, None, "square", 0.25, 2)
                              for f in (523, 659, 784, 1047)], v(0.45, 1319, None, "square", 0.25, 3)),
        "game_over": _seq(*[v(0.3, f, f * 0.97, "triangle", 0.45, 2)
                            for f in (392, 330, 262)], v(0.8, 196, 180, "triangle", 0.45, 3)),
        "victory": _seq(*[v(0.14, f, None, "square", 0.25, 1.5)
                          for f in (523, 523, 523, 659, 784, 659, 784, 1047, 1319)],
                        v(0.8, 1568, None, "square", 0.25, 2)),
        # Menus
        "menu_move": v(0.05, 660, 760, "triangle", 0.25, 2),
        "menu_select": _seq(v(0.06, 660, None, "square", 0.2, 1), v(0.12, 990, None, "square", 0.2, 2)),
        "key": v(0.04, 880, None, "triangle", 0.25, 3),
        "new_best": _seq(*[v(0.09, f, None, "sine", 0.4, 1) for f in (880, 1109, 1319, 1760)]),
    }


def _midi_freq(note):
    return 440.0 * 2 ** ((note - 69) / 12)


class Audio:
    def __init__(self, sound_volume=0.8, music_volume=0.5):
        self.sound_volume = sound_volume
        self.music_volume = music_volume
        self.enabled = False
        self.effects = {}
        self.notes = {}
        self.song = None
        self.step = 0
        self.clock = 0.0
        self.step_time = 0.1
        self.current_theme = None
        self.current_key = None
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(32)
            pygame.mixer.set_reserved(MUSIC_CHANNELS)
            self.channels = [pygame.mixer.Channel(i) for i in range(MUSIC_CHANNELS)]
            self.effects = {name: _sound(data) for name, data in _build_effects().items()}
            self.drums = {
                "kick": _sound(_voice(0.16, 150, 42, "sine", 0.9, 4)),
                "snare": _sound(_mix(_noise(0.14, 0.55, 0.8, curve=5), _voice(0.1, 210, 170, "triangle", 0.25))),
                "hat": _sound(_noise(0.04, 0.3, 1.0, curve=6, seed=9)),
            }
            self.enabled = True
        except pygame.error as error:
            print(f"Audio disabled: {error}")

    # ---- Effects --------------------------------------------------------
    def play(self, name, volume=1.0):
        if not self.enabled or self.sound_volume <= 0:
            return
        sound = self.effects.get(name)
        if sound:
            channel = sound.play()
            if channel:
                channel.set_volume(min(1.0, self.sound_volume * volume))

    def set_sound_volume(self, volume):
        self.sound_volume = volume

    def set_music_volume(self, volume):
        self.music_volume = volume

    # ---- Music ----------------------------------------------------------
    def _note(self, midi, wave, dur, curve=3.0, vol=0.5):
        key = (midi, wave, round(dur, 2))
        if key not in self.notes:
            self.notes[key] = _sound(_voice(dur, _midi_freq(midi), None, wave, vol, curve, 0.004))
        return self.notes[key]

    def _compose(self, theme, boss):
        """Turn a theme into a 4-bar loop: a list of 16th-note steps per bar."""
        rng = random.Random(theme.seed + (1000 if boss else 0))
        scale = theme.scale

        def pitch(degree, octave=0):
            d = degree % len(scale)
            o = degree // len(scale) + octave
            return theme.root + scale[d] + 12 * o

        steps_per_bar = 16
        bars = 4
        song = [[] for _ in range(steps_per_bar * bars)]
        bass_shape = rng.choice(([0, 3, 6, 8, 11, 14], [0, 4, 8, 12], [0, 2, 6, 8, 10, 14],
                                 [0, 3, 8, 11, 12]))
        if boss:
            bass_shape = list(range(0, 16, 2))
        for bar, degree in enumerate(theme.progression):
            base = bar * steps_per_bar
            for s in bass_shape:
                song[base + s].append(("note", 0, self._note(pitch(degree, -2), "triangle", 0.22, 3, 0.75), 0.75))
            chord = [degree, degree + 2, degree + 4, degree + 7]
            arp = rng.choice(([0, 1, 2, 3], [0, 2, 1, 3], [3, 2, 1, 0]))
            for s in range(0, 16, 2):
                tone = chord[arp[(s // 2) % 4]]
                song[base + s].append(("note", 1, self._note(pitch(tone, 0), "triangle", 0.16, 4, 0.5), 0.33))
            # Drums
            for s in (0, 8) if not boss else (0, 4, 8, 12):
                song[base + s].append(("drum", 3, "kick", 0.6))
            for s in (4, 12):
                song[base + s].append(("drum", 3, "snare", 0.45))
            for s in range(2, 16, 4):
                song[base + s].append(("drum", 4, "hat", 0.3))
        # A short melody that repeats, changing only at the end of the phrase
        penta = [0, 2, 4, 7, 9, 11]
        walk = rng.randrange(len(penta))
        motif = []
        for s in range(0, 32, 2):
            if rng.random() < (0.72 if boss else 0.6):
                walk = max(0, min(len(penta) - 1, walk + rng.choice((-2, -1, 1, 2))))
                motif.append((s, penta[walk]))
        for offset in (0, 32):
            for s, degree in motif:
                if offset and s >= 24:
                    continue
                song[offset + s].append(("note", 2, self._note(pitch(degree, 1), theme.lead, 0.2, 3, 0.4), 0.34))
        for s, degree in ((56, 4), (58, 2), (60, 1), (62, 0)):
            song[s].append(("note", 2, self._note(pitch(degree, 1), theme.lead, 0.2, 3, 0.4), 0.34))
        return song

    def play_theme(self, theme=MENU_THEME, boss=False):
        if not self.enabled:
            return
        key = (id(theme), boss)
        if self.current_key == key:
            return
        self.stop_music()
        self.current_key = key
        self.song = self._compose(theme, boss)
        bpm = theme.bpm + (22 if boss else 0)
        self.step_time = 60.0 / bpm / 4
        self.step = 0
        self.clock = 0.0

    def stop_music(self):
        self.song = None
        self.current_key = None
        if self.enabled:
            for channel in self.channels:
                channel.stop()

    def update(self, dt):
        """Called every frame; plays whichever music steps have come due."""
        if not self.song:
            return
        self.clock += dt
        while self.clock >= self.step_time:
            self.clock -= self.step_time
            self.step = (self.step + 1) % len(self.song)
            if self.music_volume <= 0:
                continue
            for kind, channel_index, what, volume in self.song[self.step]:
                channel = self.channels[channel_index]
                channel.play(self.drums[what] if kind == "drum" else what)
                channel.set_volume(volume * self.music_volume)
