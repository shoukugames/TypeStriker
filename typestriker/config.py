"""Game constants and the definition of all ten levels."""
from dataclasses import dataclass, field

WIDTH, HEIGHT = 960, 720
FPS = 60
TITLE = "Type Striker"

AUTHOR = "Shawn Rapaz"
WEBSITE = "https://shoukugames.org/"
EMAIL = "info@shoukugames.org"

TOP_BAR_H = 52
RAIL_Y = 590            # height of the rail the player's ship rides on
RAIL_AMPLITUDE = 330

START_LIVES = 3
MAX_HP = 10
POINTS_PER_LETTER = 100
BOSS_SHOTS = 10
BOSS_BONUS = 1000
LEVEL_CLEAR_REPAIR = 3  # hull points repaired between levels
INVULNERABLE_TIME = 2.0

TOP_SCORES = 10
NAME_LENGTH = 10

SHIP_KINDS = ("scout", "fighter", "bomber", "saucer", "interceptor", "drone")


@dataclass(frozen=True)
class Palette:
    primary: tuple
    secondary: tuple
    accent: tuple
    bullet: tuple


@dataclass(frozen=True)
class MusicTheme:
    bpm: int
    root: int           # MIDI note of the root
    scale: tuple        # semitone offsets
    progression: tuple  # scale degrees, one per bar
    lead: str           # waveform
    seed: int


MINOR = (0, 2, 3, 5, 7, 8, 10)
MAJOR = (0, 2, 4, 5, 7, 9, 11)
DORIAN = (0, 2, 3, 5, 7, 9, 10)
PHRYGIAN = (0, 1, 3, 5, 7, 8, 10)
MIXOLYDIAN = (0, 2, 4, 5, 7, 9, 10)


@dataclass(frozen=True)
class Level:
    number: int
    name: str
    tagline: str
    theme: str              # background painter
    setting: str            # "space" or "planet"
    word_length: int        # 1 = single random letters
    targets: int            # how many enemies and objects before the boss
    speed: float            # pixels per second
    spawn_interval: float   # seconds between arrivals
    max_on_screen: int
    fire_interval: float    # seconds between shots, per enemy
    bullet_speed: float
    weights: dict = field(default_factory=dict)
    palette: Palette = None
    boss: str = ""
    boss_name: str = ""
    boss_pattern: str = "aimed"
    boss_fire_interval: float = 3.0
    boss_speed: float = 60.0
    music: MusicTheme = None


LEVELS = (
    Level(1, "Earth Orbit", "The invasion begins above home.", "orbit", "space",
          1, 18, 55, 2.00, 5, 9.0, 190,
          {"scout": 6, "asteroid": 4},
          Palette((88, 128, 190), (46, 66, 112), (120, 230, 255), (120, 220, 255)),
          "warden", "THE WARDEN", "aimed", 3.4, 55,
          MusicTheme(112, 57, MINOR, (0, 5, 3, 6), "square", 11)),
    Level(2, "Asteroid Belt", "Mind the rocks, pilot!", "belt", "space",
          1, 22, 68, 1.60, 6, 8.0, 205,
          {"asteroid": 6, "scout": 2, "fighter": 2},
          Palette((176, 118, 70), (98, 66, 46), (255, 190, 80), (255, 180, 90)),
          "rockbreaker", "ROCKBREAKER", "spread3", 3.6, 65,
          MusicTheme(120, 55, DORIAN, (0, 3, 0, 4), "saw", 22)),
    Level(3, "Verdant World", "Tanks patrol the jungle below.", "forest", "planet",
          1, 26, 80, 1.30, 7, 7.0, 220,
          {"tank": 35, "scout": 25, "fighter": 25, "missile": 15},
          Palette((96, 136, 72), (56, 80, 46), (230, 240, 110), (240, 240, 110)),
          "crawler", "IRON CRAWLER", "burst", 3.4, 45,
          MusicTheme(126, 60, MIXOLYDIAN, (0, 6, 3, 0), "square", 33)),
    Level(4, "Crimson Nebula", "First words ahead: two letters each.", "nebula", "space",
          2, 22, 70, 2.00, 6, 7.0, 225,
          {"fighter": 3, "interceptor": 3, "missile": 2, "asteroid": 2},
          Palette((190, 58, 78), (104, 32, 66), (255, 170, 120), (255, 110, 150)),
          "manta", "CRIMSON MANTA", "spread3", 3.4, 80,
          MusicTheme(128, 52, PHRYGIAN, (0, 1, 5, 0), "saw", 44)),
    Level(5, "Desert World", "Three-letter words in the burning sands.", "desert", "planet",
          3, 22, 68, 2.40, 6, 6.5, 235,
          {"tank": 4, "bomber": 2, "drone": 2, "missile": 2},
          Palette((206, 158, 84), (128, 88, 50), (255, 96, 60), (255, 130, 60)),
          "scorpion", "SAND SCORPION", "burst", 3.3, 70,
          MusicTheme(132, 50, DORIAN, (0, 6, 4, 3), "square", 55)),
    Level(6, "Frozen Moon", "Four-letter words on the ice.", "ice", "planet",
          4, 22, 66, 2.70, 6, 6.0, 245,
          {"tank": 3, "saucer": 3, "fighter": 2, "asteroid": 2},
          Palette((168, 214, 240), (84, 128, 176), (90, 240, 255), (130, 230, 255)),
          "frost", "FROST FORTRESS", "fan5", 3.8, 50,
          MusicTheme(116, 62, MINOR, (5, 3, 0, 4), "sine", 66)),
    Level(7, "Ion Storm", "Five-letter words through the lightning.", "storm", "space",
          5, 22, 64, 3.00, 6, 5.5, 255,
          {"interceptor": 3, "drone": 3, "saucer": 2, "missile": 2},
          Palette((70, 196, 180), (56, 74, 130), (214, 120, 255), (190, 130, 255)),
          "stormlord", "STORM LORD", "ring", 4.2, 90,
          MusicTheme(138, 53, DORIAN, (0, 2, 3, 1), "saw", 77)),
    Level(8, "Magma World", "Six-letter words above rivers of fire.", "lava", "planet",
          6, 24, 62, 3.20, 6, 5.0, 265,
          {"tank": 3, "bomber": 2.5, "missile": 2.5, "asteroid": 2},
          Palette((86, 66, 62), (46, 36, 38), (255, 128, 30), (255, 150, 40)),
          "titan", "MAGMA TITAN", "fan5", 3.6, 55,
          MusicTheme(142, 48, PHRYGIAN, (0, 1, 0, 6), "square", 88)),
    Level(9, "Mothership Hull", "Seven-letter words on the enemy flagship.", "hull", "planet",
          7, 24, 60, 3.40, 6, 4.5, 275,
          {"tank": 3, "drone": 3, "interceptor": 2, "missile": 2},
          Palette((110, 96, 150), (58, 50, 90), (120, 255, 150), (130, 255, 170)),
          "hive", "THE HIVE CORE", "ring", 4.0, 80,
          MusicTheme(148, 51, MINOR, (0, 5, 6, 4), "saw", 99)),
    Level(10, "The Black Hole", "Eight-letter words at the edge of everything.", "blackhole", "space",
          8, 26, 60, 3.40, 7, 4.0, 290,
          {"scout": 1, "fighter": 2, "bomber": 1, "saucer": 2, "interceptor": 2,
           "drone": 2, "missile": 2, "asteroid": 2},
          Palette((108, 62, 150), (40, 26, 70), (255, 100, 220), (255, 110, 230)),
          "emperor", "VOID EMPEROR", "fan5", 3.6, 100,
          MusicTheme(156, 45, PHRYGIAN, (0, 1, 5, 3), "saw", 110)),
)

MENU_THEME = MusicTheme(100, 57, DORIAN, (0, 3, 5, 4), "sine", 7)


def describe_challenge(level):
    """Short text telling the player what they will be typing."""
    if level.word_length == 1:
        return "Single letters"
    return f"{level.word_length}-letter words"
