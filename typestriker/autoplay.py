"""A robot typist used by the tests, the screenshot tool and the build smoke test."""


class Autoplayer:
    def __init__(self, letters_per_second=4.0, mistake_rate=0.0, rng=None):
        self.interval = 1.0 / letters_per_second
        self.mistake_rate = mistake_rate
        self.rng = rng
        self.clock = 0.0

    def choose(self, scene):
        if not scene.can_type():
            return None
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
