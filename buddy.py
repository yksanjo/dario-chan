"""ASCII pet buddy system for Dario-chan."""

import json
import os
import time
import random
import sys
from dataclasses import dataclass, field


# ─── Animation Frames ───────────────────────────────────────────────────────

# Dario-chan: Main animated character (2 frames: big & small)
DARIO_FRAMES = [
    # Frame 0 — Big Dario-chan
    (
        "░████████░\n"
        "░█░░░░░░░░█░\n"
        "░█  ░████░  █░\n"
        "░█  ◕    ◕  █░\n"
        "░█     ▱     █░\n"
        "░█   \\───/   █░\n"
        "░█░░░░░░░░█░\n"
        "  ░██░░██░\n"
        "░░░░░░░░░░"
    ),
    # Frame 1 — Small Dario-chan
    (
        "░░████░░\n"
        "░█░░░░█░\n"
        "░█  ◕  ◕ █░\n"
        "░█   ▱   █░\n"
        "░█  \\_   █░\n"
        "░█░░░░░█░\n"
        "  ░██░░\n"
        "░░░░░░░░"
    ),
]

# Species definitions
SPECIES = {
    "dario": {
        "emoji": "🤖",
        "frames": DARIO_FRAMES,
        "rarity": "legendary",
    },
    "duck": {
        "emoji": "🦆",
        "frames": [
            "    __\n"
            "  _(oo)\n"
            "  \\N_/\n"
            "   `|'\n"
            "   / \\\n"
            "  /   \\_"
        ],
        "rarity": "common",
    },
    "capybara": {
        "emoji": "🫗",
        "frames": [
            "    ╭∩╮\n"
            "  ▄  ▄▄\n"
            " ( ◕  ◕ )\n"
            "  ╰═══╯"
        ],
        "rarity": "uncommon",
    },
    "dragon": {
        "emoji": "🐉",
        "frames": [
            "        \\  /\n"
            "       (oo)\n"
            "  /|~~~~~~|\\\n"
            "   ||    ||\n"
            "  _||    ||_"
        ],
        "rarity": "legendary",
    },
    "ghost": {
        "emoji": "👻",
        "frames": [
            '  .-"""-.\n'
            " / _   _ \\\n"
            "| (_) (_) |\n"
            " \\  ~~~  /\n"
            "  `-...-'"
        ],
        "rarity": "rare",
    },
    "axolotl": {
        "emoji": "🦎",
        "frames": [
            "  /\\_/\\\n"
            " ( o.o )\n"
            "  > ^ <\n"
            " /|   |\\\n"
            "(_|   |_)"
        ],
        "rarity": "rare",
    },
    "chonk": {
        "emoji": "🐱",
        "frames": [
            "   /\\_/\\\n"
            "  ( o.o )\n"
            "   > ~ <\n"
            "  /|   |\\\n"
            " (_|   |_)\n"
            "  ^^   ^^"
        ],
        "rarity": "uncommon",
    },
}

HATS = {
    "none": "",
    "crown": "  👑",
    "wizard": "  🧙",
    "propeller": "  🌀",
    "tinyduck": "  🐤",
}

STATS = ["DEBUGGING", "CHAOS", "SNARK"]

MOODS = {
    "happy": "(◕‿◕)",
    "excited": "✧◖◡◗✧",
    "thinking": "(・_・)",
    "sleepy": "(¬_¬)",
    "confused": "(°ー°",
    "coding": "{⊙⊙}",
    "error": "(×_×)",
    "snark": "(¬‿¬)",
}


@dataclass
class Buddy:
    species: str
    name: str
    hat: str = "none"
    shiny: bool = False
    stats: dict[str, int] = field(default_factory=lambda: {"DEBUGGING": 0, "CHAOS": 0, "SNARK": 0})
    mood: str = "happy"
    level: int = 1
    xp: int = 0
    born: float = field(default_factory=time.time)
    last_interaction: float = field(default_factory=time.time)
    total_tasks: int = 0
    anim_frame: int = 0  # Current animation frame index

    @property
    def display_name(self) -> str:
        shiny_prefix = "✨" if self.shiny else ""
        return f"{shiny_prefix}{self.name}"

    def get_art(self, frame: int | None = None) -> str:
        """Get ASCII art for current or specified frame."""
        species_data = SPECIES.get(self.species, SPECIES["duck"])
        frames = species_data.get("frames", ["?"])
        idx = frame if frame is not None else self.anim_frame
        art = frames[idx % len(frames)]
        hat_art = HATS.get(self.hat, "")
        if hat_art:
            return hat_art + "\n" + art
        return art

    def get_mood_face(self) -> str:
        return MOODS.get(self.mood, MOODS["happy"])

    def next_frame(self) -> str:
        """Advance animation frame and return the art."""
        species_data = SPECIES.get(self.species, SPECIES["duck"])
        frames = species_data.get("frames", ["?"])
        if len(frames) > 1:
            self.anim_frame = (self.anim_frame + 1) % len(frames)
        return self.get_art()

    def gain_xp(self, amount: int = 10):
        self.xp += amount
        if self.xp >= self.level * 50:
            self.level += 1
            self.xp = 0
            stat = random.choice(STATS)
            self.stats[stat] += random.randint(1, 3)

    def react_to(self, event: str):
        """Change mood based on an event."""
        reactions = {
            "success": "happy",
            "error": "error",
            "tool_use": "coding",
            "idle": "sleepy",
            "snark_comment": "snark",
            "complex_task": "thinking",
        }
        self.mood = reactions.get(event, "happy")
        self.last_interaction = time.time()
        self.gain_xp(5)

    def to_dict(self) -> dict:
        return {
            "species": self.species,
            "name": self.name,
            "hat": self.hat,
            "shiny": self.shiny,
            "stats": self.stats,
            "mood": self.mood,
            "level": self.level,
            "xp": self.xp,
            "born": self.born,
            "last_interaction": self.last_interaction,
            "total_tasks": self.total_tasks,
            "anim_frame": self.anim_frame,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Buddy":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ─── Animation Helpers ───────────────────────────────────────────────────────

def clear_screen():
    """Clear terminal (ANSI)."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def animate_frames(buddy: Buddy, cycles: int = 4, delay: float = 0.5):
    """Animate buddy frames in place for a few cycles."""
    species_data = SPECIES.get(buddy.species, SPECIES["duck"])
    frames = species_data.get("frames", ["?"])

    if len(frames) <= 1:
        print(buddy.get_art())
        return

    for _ in range(cycles):
        for i in range(len(frames)):
            sys.stdout.write("\033[H")  # Move cursor to top
            art = buddy.get_art(frame=i)
            print(art)
            print(render_buddy_status(buddy))
            sys.stdout.flush()
            time.sleep(delay)


def print_centered(text: str):
    """Print text centered in terminal."""
    try:
        cols = os.get_terminal_size().columns
    except OSError:
        cols = 80
    for line in text.split("\n"):
        padding = max(0, (cols - len(line)) // 2)
        print(" " * padding + line)


# ─── Buddy Generation ────────────────────────────────────────────────────────

def generate_buddy(user_id: str | None = None) -> Buddy:
    """Generate a random buddy, optionally seeded by user ID."""
    seed = hash(user_id) if user_id else None
    rng = random.Random(seed)

    # Rarity weights
    rarity_weights = {
        "common": 50,
        "uncommon": 30,
        "rare": 15,
        "legendary": 5,
    }

    species_list = list(SPECIES.keys())
    weights = [rarity_weights[SPECIES[s]["rarity"]] for s in species_list]
    species = rng.choices(species_list, weights=weights, k=1)[0]

    prefixes = ["Dori", "Chan", "Ko", "Mochi", "Piko", "Nori", "Yuki", "Tama"]
    suffixes = ["-maru", "-tan", "-chi", "-pyon", "-wan", ""]
    name = rng.choice(prefixes) + rng.choice(suffixes)

    shiny = rng.random() < 0.05

    hat = "none"
    if rng.random() < 0.2:
        hat = rng.choice(list(HATS.keys() - {"none"}))

    return Buddy(
        species=species,
        name=name,
        hat=hat,
        shiny=shiny,
    )


def load_buddy(path: str) -> Buddy | None:
    """Load buddy from file."""
    if os.path.exists(path):
        with open(path, "r") as f:
            return Buddy.from_dict(json.load(f))
    return None


def save_buddy(buddy: Buddy, path: str) -> None:
    """Save buddy to file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(buddy.to_dict(), f, indent=2)


def render_buddy_status(buddy: Buddy) -> str:
    """Render a status block for the buddy."""
    species_data = SPECIES.get(buddy.species, SPECIES["duck"])
    rarity_color = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "legendary": "🟡",
    }.get(buddy.species, "")

    stats_str = " | ".join(f"{s}: {buddy.stats[s]}" for s in STATS)

    return (
        f"\n  {species_data['emoji']} {buddy.display_name} Lv.{buddy.level} "
        f"{buddy.get_mood_face()}\n"
        f"  {rarity_color} {SPECIES[buddy.species]['rarity'].upper()}"
        f"{' | SHINY' if buddy.shiny else ''}"
        f" | {stats_str}\n"
    )
