"""A robot typist used by the tests, the screenshot tool and the build smoke test."""


class Autoplayer:
    def __init__(self, letters_per_second=4.0, mistake_rate=0.0, rng=None, dodge_rate=1.0, notice_time=0.3):
        self.interval = 1.0 / letters_per_second
        self.mistake_rate = mistake_rate
        self.rng = rng
        self.clock = 0.0
        self.dodge_rate = dodge_rate
        self.notice_time = notice_time
        self.seen = {}

    def _wants_to_dodge(self, volley):
        if volley not in self.seen:
            self.seen[volley] = self.dodge_rate >= 1.0 or self.rng.random() < self.dodge_rate
        return self.seen[volley] and volley.age >= self.notice_time

    def choose(self, scene):
        if not scene.can_type():
            return None
        if scene.dodging is not None:
            return scene.dodging.next_letter
        for volley in scene.threats():
            if self._wants_to_dodge(volley):
                return volley.next_letter
        if scene.locked is not None and scene.locked.alive and not scene.locked.doomed:
            return scene.locked.next_letter
        items = scene.typeable()
        return items[0].next_letter if items else None

    def update(self, dt, scene):
        self.clock += dt
        if self.clock < self.interval:
            return
        self.clock -= self.interval
        letter = self.choose(scene)
        if letter is None:
            self.clock = 0.0
            return
        if self.rng is not None and self.rng.random() < self.mistake_rate:
            scene.press("#")  # never matches, so it always counts as a wrong key
            return
        scene.press(letter)
