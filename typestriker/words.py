"""Child-friendly word lists and the no-repeat bags that deal them out.

Every word here was hand picked for young players. Words are grouped by length
automatically, so a word can never land in the wrong level.
tests/test_words.py checks the list against a blocklist.
"""
import random
import string
from collections import deque

_WORDS = """
am an as at be by do go he hi if in is it me my no of oh ok on or ox so to up us we ad
ah aw ha ma pa yo ow um uh hm

ant ape apt arc ark arm art ash ask ate bag bat bay bed bee bib big bin bit bow box boy
bud bug bun bus but buy cab cam can cap car cat cod cog cow cry cub cup cut dad day den
dew dig dim dip dog dot dry dug ear eat eel egg elf elk elm emu end eve eye fan far fed
fee few fig fin fir fit fix fly fog for fox fun fur gap gas gem get gum ham has hat hay
hen her hid him hip his hop hot how hub hug hum ice icy ink inn ivy jam jar jaw jet job
jog joy jug key kid kit lab lad lap law lay leg let lid lip lit log lot low map mat may
men met mix mom mop mud mug nap net new nod nor not now nut oak oar oat odd off oil old
one orb our out owl own pad pal pan paw pay pea pen pet pie pig pin pit pod pop pup put
ram ran rat raw ray red rib rid rim rod row rub rug run rye sad sap sat saw say sea see
set sew she shy sip sir sit six ski sky sly son spa spy sum sun tab tag tan tap tax tea
ten the tie tin tip toe ton top toy try tub tug two urn use van vat vet vow wag was wax
way web wet who why wig win wit wok won wow yak yam yes yet you zap zip zoo

able acid aged also arch area army aunt away baby back bake ball band bank barn base
bath bead beak bean bear beat bell belt bend best bike bird bite blue boat bold bolt
bone book boot born both bowl brow bump burn bush busy cage cake calf call calm came
camp card care cart case cave cent chef chin chip city clam clap claw clay clip club
coal coat code coin cold comb come cone cook cool copy cord corn cost cozy crab crew
crow cube cute dark dart dash data dawn deal deck deep deer desk dial dice dime dirt
dish dive dock does doll dome done door dove down drag draw drip drum duck dune dusk
dust each earn east easy edge else even ever face fact fair fall farm fast fawn feed
feel feet fern file fill film find fine fire firm fish five flag flap flat flew flip
flow foam fold food foot fork form fort four free frog from fuel full game gate gave
gear gift give glad glow glue goal goat gold golf gone good gown grab gray grew grid
grin grip grow gulf hair half hall hand hare harp have hawk head heal heat help herb
here hero hide high hike hill hint hive hold hole home hood hook hoop hope horn huge
idea inch iron item jade jazz join joke jump june just keen keep kept kind king kite
kiwi knee knew knit knot know lace lake lamb lamp land lane last late lava lawn lead
leaf lean left lens less life lift like lily lime line lion list live load loaf long
look loud love luck lung made mail main make many mark mask mast math maze meal mean
meet melt menu mice mild milk mind mine mint mist moat mole moon more moss most move
much name navy near neat neck need nest news next nice nine node nose note oboe okay
once only onto open oval oven over pace pack page pail pair palm park part past path
peak pear pick pier pine pink pipe plan play plot plug plum poem poet pole polo pond
pony pool port post prop pull pump pure push quiz race raft rail rain rake ramp rang
rate read real reef rest rice rich ride ring ripe rise road roar rock roll roof room
root rope rose ruby rule rush safe sage said sail salt same sand sang save seal seat
seed seek seem self sell send ship shoe shop show side sign silk sing sink size skip
slam sled slid slim slow snow soap sock sofa soft soil sold sole some song soon sort
soup sour spin spot star stay stem step stew stop such suit sung sure swan swim tail
take tale talk tall tame tank tape task team teal tell tent term test than that them
then they thin this tide tile time tiny tire toad tofu told tone took tool tour town
tray tree trim trip true tube tuna tune turn twin type unit upon used vase vast very
vest view vine visa vote wade wait wake walk wall want warm wash wave wavy weak wear
week well went were west what when wide wild will wind wing wink wise wish wolf wood
wool word wore work wrap yard yarn year yoga your zero zone zoom

about above actor adapt adopt adult after again agree ahead album alien align alike
alive allow alone along alpha amber among angel angle ankle apple apply april apron
arena argue arise armor arrow aside atlas attic award aware bacon badge bagel baker
basic basin basil beach beads beans beard begin being bench berry bison black blank
blaze blend bliss block bloom blown board boost booth bored bound brain brake brand
brave bread break brick bride brief bring brisk broad broke brook broom brown brush
build built bunch bunny cabin cable camel candy canoe cargo carry catch cause cedar
chain chair chalk champ charm chart chase cheek cheer chess chest chick chief child
chime chips choir chord chose civic claim class clean clear clerk click cliff climb
clock close cloth cloud clove clown coach coast cocoa color comet comic coral couch
count court cover crane crawl cream creek crisp cross crowd crown crust cubic curve
cycle daily daisy dance dealt delta depth diary digit diner ditch diver dizzy dodge
donut doubt dough dozen draft drain drama drank drawn dream dress dried drift drink
drive drove dunes eagle early earth eight elbow elder elect elves email empty enjoy
enter equal error essay event every exact extra fable fairy faith false fancy feast
fence ferry fever fiber field fifth fifty final finch first flame flash fleet flint
float flock flood floor flour fluff fluid flute focus force forge forth forty forum
found frame fresh front frost fruit fudge fully funny gauge gecko genie giant glass
gleam glide globe glove going goose grace grade grain grand grant grape graph grasp
grass great green greet grill groom group grove guard guess guest guide habit happy
harsh haven hazel heart heavy hedge hello hippo hobby holly honey honor horse hotel
house human humor hurry icing ideal igloo image inner input irony ivory jelly jewel
jolly judge juice jumbo kayak kitty knack kneel knock koala label lance large laser
later laugh layer learn lemon level light lilac limit linen llama lobby local lodge
logic lotus lucky lunar lunch magic major maker mango maple march marsh match maybe
mayor medal melon merit merry metal meter midst might minor mixed model money month
moose motor mount mouse mouth movie music nacho naval nerve never night ninth noble
noise north novel nurse nylon ocean offer often olive onion opera orbit order organ
other otter outer owner oxide paint panda panel paper party pasta patch pause peace
peach pearl pedal penny perch petal phone photo piano piece pilot pizza place plain
plane plant plate plaza plump point polar pouch pound power press price pride prime
print prism prize proof proud prove puppy purse quack queen quest quick quiet quilt
quite radar radio rainy raise rally ranch range rapid raven reach react ready realm
relax relay reply rhyme rider ridge right rinse river roast robin robot rocky round
route royal ruler rural salad sandy sauce scale scarf scene scoop score scout shade
shake shape share shark sharp sheep sheet shelf shell shine shiny shirt shore short
sight silly since sixth sixty skate skill skirt sleep slept slice slide small smart
smile smith snack snail snake sneak solar solid solve sound south space spare spark
speak speed spell spend spice spike spoon sport spray squid stack staff stage stair
stamp stand start state steam steel steep stick still stone stood store storm story
stove straw study stuff style sugar sunny super swift swing table taste teach teeth
thank theme thick thing think third those three threw thumb tiger tight timer title
toast today token tooth topic torch total touch tower track trade trail train treat
trend trial tribe trick truck truly trunk trust truth tulip tutor twice twist uncle
under union unity until upper urban usual valid value vapor video visit vital vivid
vocal voice wagon walls waltz watch water whale wheat wheel where which while white
whole width wings witty woman world worth woven wrist write yacht young youth zebra

absorb accept across action active actual advice agreed almond always amount animal
annual answer appeal appear arctic around arrive artist aspect asleep autumn avenue
badger bakery ballet bamboo banana banner barley basket beacon beaver became become
before behind belong better beyond billow binder blazer blouse bobcat bonnet border
bottle bottom bounce branch breeze bridge bright broken bronze bubble bucket budget
bumper bundle butter button cactus camera campus candle canyon carbon carpet carrot
castle casual cattle cereal chance change charge cheese cherry chosen circle citrus
clever client climbs closer clover cobalt coffee collar colony column comedy common
cookie copper corner cotton county cousin cradle crater create cheers cruise custom
daring decide degree desert design detail dinner direct doctor dollar domain donkey
double dragon drawer driver during easily eating effort eighty either eleven emblem
empire enable energy engine enough entire equals escape estate expert fabric facing
factor falcon family famous farmer father fellow fiddle figure finish flight flower
flying forest forget formal fossil friend frozen future galaxy garden garlic gather
gentle gerbil giggle ginger glider global golden gopher grapes gravel ground growth
guitar hammer hamlet handle happen harbor hazard health helmet hermit hidden hiking
hockey honest hopper hornet humble iguana impact indoor inside invent island jacket
jaguar jersey jigsaw jingle jockey jogger jumper jungle junior kettle kitten knight
ladder lagoon launch leader league legend lemons lesson letter lively lizard locket
lumber magnet mammal manner marble margin marine market marvel master meadow medium
melody member memory mentor mirror mitten mobile modern moment monkey moving museum
muffin mutual myself narrow nature nearby needle nephew nickel nimble nobody normal
notice number nutmeg object office option orange orchid origin outfit oxygen oyster
packet paddle palace pantry parade parrot pastel peanut pebble pencil people pepper
period pickle picnic pigeon pillow planet player pocket poetry policy pollen potato
powder pretty prince puddle puppet purple puzzle python rabbit racket radish rafter
random ranger rarely rather reader reason recipe record reduce reflex refuge relief
remote repair report rescue result ribbon riddle rocket rodent rubber runner saddle
safari safety sailor salmon sample school screen search season second secret select
shadow shield silver simple singer sister sketch sleepy slower smooth snacks soccer
socket spirit splash spring sprout square squash stable stairs statue steady stereo
sticky stream street strong studio submit summer sunset supply surely switch symbol
system tablet tackle talent target temple tennis thirty thread throne ticket timber
tomato tongue toucan toward travel treaty trophy tunnel turkey turtle twelve twenty
unique unlock useful valley vanish velvet violet vision volume voyage waffle walnut
wander weaver weekly window winner winter wisdom wizard wonder wooden worthy yellow
zipper zodiac

academy achieve acrobat address advance adviser airline airport alchemy almanac already
amazing ancient antenna anybody applaud apricot archive arrange article artwork athlete
attract auction average awesome balance balcony balloon bananas bargain battery bedroom
beehive believe benefit between bicycle biscuit blanket blender blossom bluejay bouquet
bowling bracket bravery breathe brother buffalo builder bulldog cabbage cabinet caboose
calcium camping candies capable captain caravan careful caribou cartoon cascade catalog
catcher ceiling central century ceramic certain chamber channel chapter charity checker
chicken chimney chipper citizen classic cleaner clearly climate climber clothes coastal
collect college comfort command comment company compare compass concert connect contain
contest control cookies correct costume cottage counter country courage cowgirl crayons
creator creature cricket crimson crystal culture cupcake curious current curtain cushion
cyclone dancing daytime deliver dentist desktop dessert diamond digital discuss display
distant diverse dolphin doorway drawing dreamer drizzle driving eagerly eastern ecology
edition educate elegant element elevate emerald emperor enchant engaged enhance enlarge
equator evening example excited exhibit explain explore express extreme factory fantasy
farmers fashion feather feature festive fiction fifteen finally firefly fishing fitness
flannel flipper florist forever fortune forward founder fragile freedom freight friends
frisbee gallery garment gateway general genuine gesture giraffe glacier glimmer glitter
glowing gondola gorilla grammar granite grapple graphic gravity greeted grocery growing
habitat haircut halfway hamster handful harmony harvest headset healthy hearing helpful
helping herself highway himself history holiday hopeful horizon hostess however hundred
hydrant iceberg imagine improve include insight inspire instead invited jackpot jasmine
journal journey jubilee juggler kayaker kingdom kitchen knitted lantern laundry leaders
learner leisure lettuce library lighter limited lobster logical luggage lullaby machine
magenta magical mailbox mammoth mansion mapping marbles marimba martian meaning measure
mermaid message million mineral minimum miracle mission mixture monarch monitor morning
mystery natural neither network nightly noodles notable nothing nurture octagon october
officer olympic opening operate opinion orchard organic ostrich outdoor outline outside
overall pajamas pancake panther parents parking partner passage pattern payment peacock
pelican penguin pianist picture pilgrim pioneer planets plastic platter playful pleased
plumber popcorn popular portion postage postman pottery prairie present primary printer
problem process product program project protect provide puffins pumpkin quality quantum
quarter quickly rainbow reading realize receive recital recycle reflect regular related
reptile request respect resting restore reunion revenue rewrite rhubarb roadway rooster
rotunda routine sailing sandbox sandals satisfy sausage science scooter scratch seaweed
section sensory serious service shelter sherbet shimmer shuttle sincere skating skyline
snowman someone special spinach splashy sponsor stadium stamina station stellar sticker
storage student subject success suggest sunbeam sunrise support surface surfing surname
sweater swimmer teacher telling terrain textile theater thirsty thought thunder tourist
towards tractor traffic trainer treetop triumph trumpet tugboat turbine typical unicorn
uniform unknown upgrade upright usually utility vanilla variety various vehicle version
victory village visible visitor vitamin volcano voyager walking weather webpage website
wedding weekend welcome western whisper whistle willing windows wishful without wonders
workout worldly writing

absolute abundant accurate activity adorable airplane alphabet amethyst anything
aquarium armchair artistic asteroid attitude audience aviation backyard balanced
ballroom baseball bathroom bedrooms behavior birthday blizzard bluebird boarding
bookcase bookmark bookworm boundary bracelet brighter broccoli brochure brownies
building bungalow business calendar campfire campsite capacity captains cardinal
carefree carnival carousel category ceremony champion changing charcoal charming
cheerful children chipmunk classics classify clinging clothing coaching coconuts
collects colorful combined commerce complete computer concrete confetti consider
contains continue cookbook creative crossing cucumber customer daffodil database
daughter daydream december decorate delicate delivery designer dinosaur directly
discover distance doorbell doughnut downtown dragster dreaming dressing driveway
dumpling eggplant electric elephant elevator emeralds emphasis employee endeavor
engineer enormous envelope equality estimate evenings everyday everyone exercise
explorer exciting fabulous familiar farmland favorite february feathers festival
finished firework fireside fishbowl flagpole flamingo flashing flexible floating
flooring flourish football footstep forecast forehead forestry fountain fourteen
freezing friendly frontier frosting fruitful function funniest gardener gathered
generous geometry gigantic glorious goldfish goodness graceful graduate grandson
grateful gumdrops gymnasts habitats hallways handbook handmade handsome happened
happiest hardware harmless hedgehog heritage highland hillside historic homework
honestly horizons hospital humidity hydrogen icebergs identify illusion imagined
included increase indicate infinite informed insights instinct intended interest
internet invented inventor jamboree jetliner journals joyfully junction juvenile
kangaroo keyboard keystone kindness kingfish knapsack knitting labrador ladybird
landmark language laughter lavender learning leftover lemonade lifeboat lifetime
lighting lightbox likewise limerick listener literary location lollipop longitude
lovebird luminous magazine magician magnetic mainland marigold marmoset material
measured mechanic medicine melodies memories merchant midnight mischief moisture
momentum monorail moonbeam mosquito mountain movement mushroom musician national
navigate necklace neighbor newsroom nineteen notebook november numerous nutrient
observer obstacle occasion offering opposite optimist orbiting orchards ordinary
organize original ornament outdoors overcoat overhead overland overlook paintbox
painting pancakes parakeet parallel particle passport pastries pathways patience
pavement peaceful perfumes periodic personal petunias pictures pinecone pinwheel
plankton playback playtime pleasant positive possible practice precious prepared
preserve presents pretzels princess printing probably problems progress property
provided pumpkins purchase question quotient railroad rainfall rainbows reaction
reindeer relative remember research resident resource response restored returned
rocketry roommate rosemary sailboat sandwich sapphire scenario schedule scissors
scooters seashell seasonal security sentence separate shamrock shoelace shoulder
sidewalk signpost silently skylight skipping slippers snowball snowfall snowshoe
software solution sometime somewhere songbird southern spaceman speaking spectrum
sprinkle squirrel stairway standard starfish starship stepping sterling stingray
stitches straight strategy strength stronger students studying sunlight sunshine
superior surprise sweeping swimming sycamore syllable teaching teammate teenager
telegram terminal terrific textbook thankful thirteen thousand thoughts together
tomorrow tortoise tracking training treasure triangle tricycle tropical trousers
turnover umbrella underway uniforms universe upstairs vacation valuable velocity
vertical vineyard visitors vitamins volcanic wardrobe waterway weekends wellness
whenever wildlife windmill wireless wondrous woodland workshop yearbook yourself
zucchini
"""


_ALL = set(_WORDS.split())
WORDS_BY_LENGTH = {
    length: tuple(sorted(w for w in _ALL if len(w) == length)) for length in range(2, 9)
}
LETTERS = tuple(string.ascii_lowercase)


class Bag:
    """Deals items in shuffled order and reshuffles only when empty.

    Nothing repeats until the whole pool has been used. On reshuffle the most
    recently used items go to the back, so a repeat is always far apart.
    """

    def __init__(self, items, rng):
        self.items = list(items)
        self.rng = rng
        self.pile = deque()
        self.recent = deque(maxlen=max(1, len(self.items) // 3))

    def _refill(self):
        recent = set(self.recent)
        fresh = [i for i in self.items if i not in recent]
        stale = [i for i in self.items if i in recent]
        self.rng.shuffle(fresh)
        self.rng.shuffle(stale)
        self.pile = deque(fresh + stale)

    def draw(self, avoid_first=()):
        """Take the next item, preferring one whose first letter is not in avoid_first."""
        if not self.pile:
            self._refill()
        choice = self._first_allowed(avoid_first)
        if choice is None:
            # What's left all clashes, so deal the next shuffle behind it
            left = list(self.pile)
            self._refill()
            self.pile = deque(left + [i for i in self.pile if i not in left])
            choice = self._first_allowed(avoid_first) or self.pile[0]
        self.pile.remove(choice)
        self.recent.append(choice)
        return choice

    def _first_allowed(self, avoid_first):
        return next((c for c in self.pile if c[0] not in avoid_first), None)


class WordDealer:
    """One set of no-repeat bags that lasts for a whole game."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.bags = {1: Bag(LETTERS, self.rng)}
        for length, words in WORDS_BY_LENGTH.items():
            self.bags[length] = Bag(words, self.rng)

    def deal(self, length, avoid_first=()):
        return self.bags[length].draw(avoid_first)
