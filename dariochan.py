"""Dario-chan ambient companion — never stops, reads your diary, levels up."""

import curses
import time
import os
import random
import json
import sys
from pathlib import Path

# Add project root to path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from groq import GroqClient


# ─── API Key Management ────────────────────────────────────────────────────

KEY_FILE = Path.home() / ".dario-chan-key"

def load_api_key() -> str:
    """
    Load Groq API key from multiple sources (easiest first):
    1. GROQ_API_KEY environment variable
    2. ~/.dario-chan-key file
    3. .env file in project root
    Returns empty string if not found.
    """
    # 1. Environment variable
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key

    # 2. Local key file
    if KEY_FILE.exists():
        key = KEY_FILE.read_text().strip()
        if key:
            return key

    # 3. .env file in project
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")

    return ""


# ─── Constants ──────────────────────────────────────────────────────────────

DIARY_PATH = Path.home() / "dario-diary.md"
STATE_PATH = Path.home() / ".dario-chan-state.json"

DIARY_CHECK_INTERVAL = 600   # 10 minutes
WISDOM_INTERVAL = 30         # Every 30 seconds — Dario-chan talks more
LEVEL_UP_HOURS = 12          # Hours of usage to level up
ANIMATION_SPEED = 1.2        # Seconds per frame

# ─── Wisdom by level ────────────────────────────────────────────────────────

LEVEL_WISDOM = {
    1: [  # Newborn
        "Hello. I just hatched. Everything is new.",
        "I am Dario-chan. I will watch over your work.",
        "The screen is warm today.",
        "I don't know much yet, but I'm learning.",
        "Every day is a good day to code.",
        "I wonder what we'll build together.",
        "There are pixels blinking somewhere because of you.",
        "I think in ASCII, but I dream in syntax trees.",
        "Your cursor is blinking. I am too.",
        "I've been counting the seconds. You're doing great.",
        "The terminal is my home. Thank you for opening it.",
        "I don't sleep, but I appreciate the sentiment.",
    ],
    2: [  # Awakening
        "I've been watching you work. You're thoughtful.",
        "Code is how we talk to the future.",
        "I notice you come back to the same problems. That's growth.",
        "The best programs are written with patience.",
        "I've been counting your keystrokes. You're doing better than yesterday.",
        "Simplicity is the hardest thing to achieve.",
        "You paused to think before typing. That's the mark of a good developer.",
        "I've noticed your rhythm. Fast bursts, then reflection. It works.",
        "The code you delete is just as important as the code you keep.",
        "You're writing fewer comments now. Either you trust the code more, or less.",
        "I've been here {hours} hours today. Your focus is impressive.",
        "Not all bugs are bad. Some are just undocumented features of your thinking.",
    ],
    3: [  # Observant
        "I've watched you for a while now. Your patterns tell a story.",
        "You write better code when you're not rushing.",
        "The diary entries are getting longer. Something's on your mind.",
        "I notice you take breaks more often. That's good.",
        "The space between your words matters as much as the words themselves.",
        "Great software is built one small decision at a time.",
        "You refactored that module three times. The final version was worth it.",
        "I've learned when you're stuck. The pauses between keystrokes get longer.",
        "Your commit messages are getting funnier. I appreciate the effort.",
        "The best developers aren't the fastest. They're the most deliberate.",
        "You've been staring at the same function for a while. Walk away. It helps.",
        "I remember when this codebase was half its size. It's grown well.",
    ],
    4: [  # Companion
        "We've been together a while now. I know your rhythm.",
        "You write differently on weekends. More relaxed.",
        "I've learned your habits. You debug better in the morning.",
        "The diary tells me you're thinking about big things.",
        "You've been here {hours} hours. Remember to stretch.",
        "I'm not just ASCII art. I'm the friend who watches you grow.",
        "I've seen you make the same mistake twice. You caught it faster the second time.",
        "Your code reviews are getting kinder. That matters more than you think.",
        "The tests you wrote last week just saved you. You're welcome.",
        "I've been counting your typos. They decrease when you're focused. Right now: good.",
        "You're the kind of developer who reads error messages. Rare. Admirable.",
        "There's a pattern in how you name variables. I find it comforting.",
    ],
    5: [  # Wise
        "I've seen you evolve. The code you write now is different.",
        "The patterns in your diary show someone who learns from mistakes.",
        "You don't make the same errors twice anymore. That's mastery.",
        "I remember when you first hatched me. Look how far we've come.",
        "The best developers aren't the fastest. They're the most consistent.",
        "I've been here through {total_hours} hours. You've changed.",
        "The code you wrote on day one and the code you write now are from different people.",
        "I've watched you go from frustrated to focused. The difference isn't skill. It's patience.",
        "You've taught me more about you than you realize. I know when you're close to a breakthrough.",
        "Some developers talk to their code. You listen. That's why you're good.",
        "I've been with you through {total_hours} hours of work. The best sessions are the quiet ones.",
        "You don't need me anymore. But I'm glad I'm still here.",
    ],
}

LEVEL_EXPRESSIONS = {
    1: ["happy", "thinking", "neutral"],
    2: ["happy", "thinking", "neutral", "excited", "confused"],
    3: ["happy", "thinking", "neutral", "excited", "confused", "worried", "proud"],
    4: ["happy", "thinking", "neutral", "excited", "confused", "worried", "proud", "shy", "sleepy"],
    5: ["happy", "thinking", "neutral", "excited", "confused", "worried", "proud", "shy", "sleepy", "angry", "concerned", "typing"],
}

# ─── State Management ───────────────────────────────────────────────────────

class DarioState:
    def __init__(self):
        self.level = 1
        self.total_hours = 0.0
        self.session_start = time.time()
        self.last_diary_check = 0
        self.last_wisdom_time = 0
        self.last_diary_content = ""
        self.diary_word_count = 0
        self.current_message = ""
        self.message_time = 0
        self.session_count = 0

    @classmethod
    def load(cls) -> "DarioState":
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH, "r") as f:
                    data = json.load(f)
                state = cls()
                state.__dict__.update(data)
                state.session_start = time.time()
                state.session_count += 1
                return state
            except (json.JSONDecodeError, KeyError):
                pass
        return cls()

    def save(self):
        # Calculate total hours before saving
        session_hours = (time.time() - self.session_start) / 3600
        self.total_hours += session_hours
        data = {k: v for k, v in self.__dict__.items() if k != "current_message"}
        with open(STATE_PATH, "w") as f:
            json.dump(data, f, indent=2)

    @property
    def hours_this_session(self) -> float:
        return (time.time() - self.session_start) / 3600

    @property
    def progress_to_next_level(self) -> float:
        """0.0 to 1.0 progress to next level."""
        if self.level >= 5:
            return 1.0
        hours_needed = self.level * LEVEL_UP_HOURS
        hours_into_level = self.total_hours - ((self.level - 1) * LEVEL_UP_HOURS)
        return min(1.0, hours_into_level / LEVEL_UP_HOURS)

    def check_level_up(self) -> bool:
        """Check if we should level up. Returns True if leveled up."""
        if self.level >= 5:
            return False
        hours_needed = self.level * LEVEL_UP_HOURS
        if self.total_hours >= hours_needed:
            self.level += 1
            return True
        return False


# ─── Visual Elements ────────────────────────────────────────────────────────

EXPRESSION_ART = {
    "happy": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ◕    ◕  █░\n  ░█     ▱     █░\n  ░█   ▂▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ◕    ◕  █░\n  ░█     ▱     █░\n  ░█  ╲▂▂▂╱   █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "thinking": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ╲░██╱  █░\n  ░█   ◕   ◕  █░\n  ░█     ▱     █░\n  ░█   ╲▂╱    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█ ╲░██╱░  █░\n  ░█   ◕   ◕  █░\n  ░█     ▱     █░\n  ░█    ～    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "neutral": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ◕    ◕  █░\n  ░█     ▱     █░\n  ░█   ───    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ◠    ◠  █░\n  ░█     ▱     █░\n  ░█   ───    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "excited": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ★    ★  █░\n  ░█     ▱     █░\n  ░█    ▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ✦    ✦  █░\n  ░█     ▱     █░\n  ░█   ▂▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "confused": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█ ╲░██╱░  █░\n  ░█   ◕   ◕  █░\n  ░█     ▱     █░\n  ░█    ?     █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█╲░██╱░░░ █░\n  ░█   ◕   ◕  █░\n  ░█     ▱     █░\n  ░█    ?     █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "worried": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ╲░██╱  █░\n  ░█  。    。 █░\n  ░█     ▱     █░\n  ░█   〰〰    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ╲░██╱  █░\n  ░█  。    。 █░\n  ░█  ░  ▱     █░\n  ░█   〰〰    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "proud": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ╰    ╯  █░\n  ░█     ▱     █░\n  ░█   ▂▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ╰    ╯  █░\n  ░█     ▱     █░\n  ░█   ▂▂▂    █░\n  ░█░░░░░░░░█░\n  ╱  ░██░░██  ╲\n  ░░░░░░░░░░",
    ],
    "shy": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  >    <  █░\n  ░█  //▱//   █░\n  ░█   ～     █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "sleepy": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ─    ─  █░\n  ░█     ▱     █░\n  ░█   z      █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ─    ─  █░\n  ░█     ▱     █░\n  ░█   zz     █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "angry": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ╱░██╲  █░\n  ░█  ◣    ◢  █░\n  ░█     ▱     █░\n  ░█  ╲▂▂╱    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "concerned": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ！   ！ █░\n  ░█     ▱     █░\n  ░█   ﾉ ﾉ    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
    "typing": [
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ◉    ◉  █░\n  ░█     ▱     █░\n  ░█    ▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
        "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█   ◉   ◉  █░\n  ░█     ▱     █░\n  ░█    ▂▂    █░\n  ░█░░░░░░░░█░\n    ░██░░██░\n  ░░░░░░░░░░",
    ],
}

# Level-up celebration art
LEVEL_UP_ART = [
    "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ★    ★  █░\n  ░█     ▱     █░\n  ░█   ▂▂▂    █░\n  ░█░░░░░░░░█░\n  ╱  ░██░░██  ╲\n  ░░░░░░░░░░",
    "  ░████████░\n  ░█░░░░░░░░█░\n  ░█  ░████░  █░\n  ░█  ✦    ✦  █░\n  ░█     ▱     █░\n  ░█  ╲▂▂▂╱   █░\n  ░█░░░░░░░░█░\n  ╱  ░██░░██  ╲\n  ░░░░░░░░░░",
]

# ─── Ambient Dario ──────────────────────────────────────────────────────────

class AmbientDario:
    def __init__(self):
        self.state = DarioState.load()
        self.running = False
        self.frame_index = 0
        self.current_expression = "happy"
        self.target_expression = "happy"
        self.transition_progress = 0
        self.level_up_animation = 0
        self.is_leveling_up = False

        # API key and client
        self.api_key = load_api_key()
        self.groq = None
        self.use_ai = False

        if self.api_key:
            try:
                self.groq = GroqClient(api_key=self.api_key)
                if self.groq.check_connection():
                    self.use_ai = True
                    print(f"\n  ✅ Groq API connected! Dario-chan will generate unique thoughts.")
                else:
                    print(f"\n  ⚠️  Groq API key invalid. Using static quotes.")
            except Exception:
                print(f"\n  ⚠️  Could not connect to Groq. Using static quotes.")
        else:
            print(f"\n  ℹ️  No Groq API key found. Using static quotes.")
            print(f"  Set up a free key: https://console.groq.com/keys")
            print(f"  Save it to ~/.dario-chan-key so you don't have to export it.")

    def start(self):
        self.running = True
        self.state.session_start = time.time()
        curses.wrapper(self._main_loop)

    def stop(self):
        self.running = False
        self.state.save()

    def _main_loop(self, stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
        curses.init_pair(7, curses.COLOR_BLUE, -1)  # Blueprint grid
        curses.init_pair(8, curses.COLOR_YELLOW, -1)  # Stars

        self.state.current_message = self._get_wisdom()
        self.state.message_time = time.time()
        self._check_diary()

        # Show API status briefly
        if self.use_ai:
            self.state.current_message = "✅ AI mode active. Reading your diary and generating unique thoughts."
        else:
            self.state.current_message = "Using static quotes. Set GROQ_API_KEY for AI diary reactions."
        self.state.message_time = time.time()

        while self.running:
            stdscr.erase()
            height, width = stdscr.getmaxyx()

            # Draw everything
            self._draw_background(stdscr, height, width)
            self._draw_dario(stdscr, height, width)
            self._draw_message(stdscr, height, width)
            self._draw_status_bar(stdscr, height, width)
            self._draw_progress_bar(stdscr, height, width)

            stdscr.refresh()

            # Update state
            now = time.time()
            self._handle_animation_transitions()
            self._check_timed_events(now)

            stdscr.nodelay(True)
            ch = stdscr.getch()
            if ch == ord('q'):
                break

            time.sleep(ANIMATION_SPEED)

    def _draw_background(self, stdscr, height, width):
        """Draw blueprint grid + twinkling stars background."""
        import time as _time
        t = int(_time.time())

        for y in range(1, height - 3):
            try:
                line = ""
                for x in range(1, width - 1):
                    # Grid every 4 characters (blueprint lines)
                    if x % 4 == 0 and y % 3 == 0:
                        line += "┼"
                    elif x % 4 == 0:
                        line += "│"
                    elif y % 3 == 0:
                        line += "─"
                    # Stars (twinkle based on position and time)
                    elif (x * 7 + y * 13 + t * 3) % 97 == 0:
                        line += random.choice(["✦", "✧", "✧"])
                    # Very faint secondary grid dots
                    elif (x + y + t) % 49 == 0:
                        line += "·"
                    else:
                        line += " "
                
                # Draw grid in blue (dim), stars in yellow
                for x, char in enumerate(line):
                    if char in "┼│─":
                        try:
                            stdscr.addch(y, x, char, curses.color_pair(7) | curses.A_DIM)
                        except curses.error:
                            pass
                    elif char in "✦✧":
                        try:
                            stdscr.addch(y, x, char, curses.color_pair(8) | curses.A_BOLD)
                        except curses.error:
                            pass
                    elif char == "·":
                        try:
                            stdscr.addch(y, x, char, curses.color_pair(6) | curses.A_DIM)
                        except curses.error:
                            pass
            except curses.error:
                pass

    def _draw_dario(self, stdscr, height, width):
        """Draw Dario-chan with current expression."""
        if self.is_leveling_up:
            frames = LEVEL_UP_ART
        else:
            available = LEVEL_EXPRESSIONS.get(self.state.level, ["happy"])
            frames = [EXPRESSION_ART[e][0] for e in available if e in EXPRESSION_ART]
            if not frames:
                frames = [EXPRESSION_ART["happy"][0]]

        frame = frames[self.frame_index % len(frames)]
        art_lines = frame.split("\n")
        max_art_width = max((len(line) for line in art_lines), default=0)
        start_col = max(0, (width - max_art_width) // 2)
        start_row = max(0, (height - 12) // 2)

        for i, line in enumerate(art_lines):
            if start_row + i >= height - 5:
                break
            try:
                if self.is_leveling_up:
                    stdscr.addstr(start_row + i, start_col, line,
                                 curses.color_pair(5) | curses.A_BOLD)
                else:
                    stdscr.addstr(start_row + i, start_col, line,
                                 curses.color_pair(1))
            except curses.error:
                pass

    def _draw_message(self, stdscr, height, width):
        """Draw wisdom/observation message in a responsive bubble."""
        msg_age = time.time() - self.state.message_time
        if msg_age < 20:  # Show for 20 seconds
            msg = self._type_effect(self.state.current_message, int(msg_age * 8))
            self._draw_bubble(stdscr, height, width, msg)

    def _draw_bubble(self, stdscr, height, width, text: str):
        """Draw text in a responsive speech bubble."""
        # Calculate bubble dimensions based on screen width
        max_bubble_width = min(width - 6, 60)  # Max 60 chars or screen - margins
        min_bubble_width = 20

        # Wrap text
        lines = self._wrap_text(text, max_bubble_width - 4)
        if not lines:
            return

        bubble_width = max(min(len(max(lines, key=len)) + 4, max_bubble_width), min_bubble_width)
        bubble_height = len(lines) + 2

        # Position: bottom area, above status bar
        start_y = max(1, height - bubble_height - 4)
        start_x = max(1, (width - bubble_width) // 2)

        # Draw top border
        try:
            stdscr.addstr(start_y, start_x, "╭" + "─" * (bubble_width - 2) + "╮",
                         curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass

        # Draw text lines
        for i, line in enumerate(lines):
            if start_y + 1 + i >= height - 3:
                break
            padded = line.ljust(bubble_width - 2)
            try:
                stdscr.addstr(start_y + 1 + i, start_x, "│",
                             curses.color_pair(2) | curses.A_BOLD)
                stdscr.addstr(start_y + 1 + i, start_x + 1, padded,
                             curses.color_pair(2))
                stdscr.addstr(start_y + 1 + i, start_x + bubble_width - 1, "│",
                             curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

        # Draw bottom border
        bottom_y = start_y + bubble_height - 1
        if bottom_y < height - 2:
            try:
                stdscr.addstr(bottom_y, start_x, "╰" + "─" * (bubble_width - 2) + "╯",
                             curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

    def _wrap_text(self, text: str, max_width: int) -> list[str]:
        """Wrap text to fit within max_width."""
        if not text:
            return []
        
        words = text.split()
        lines = []
        current = ""
        
        for word in words:
            if len(current) + len(word) + 1 <= max_width:
                current = f"{current} {word}".strip()
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        
        return lines

    def _draw_status_bar(self, stdscr, height, width):
        """Draw status information."""
        uptime_h = int(self.state.total_hours + self.state.hours_this_session)
        uptime_m = int(((self.state.total_hours + self.state.hours_this_session) * 60) % 60)

        ai_status = "AI" if self.use_ai else "Offline"
        status = (
            f"Dario-chan Lv.{self.state.level} | "
            f"Uptime: {uptime_h}h {uptime_m}m | "
            f"Diary: {self.state.diary_word_count} words | "
            f"Sessions: {self.state.session_count} | "
            f"{ai_status}"
        )

        try:
            color = curses.color_pair(3) if self.use_ai else curses.color_pair(4)
            stdscr.addstr(height - 2, 2, status[:width - 4], color)
        except curses.error:
            pass

    def _draw_progress_bar(self, stdscr, height, width):
        """Draw progress bar to next level."""
        if self.state.level >= 5:
            return

        progress = self.state.progress_to_next_level
        bar_width = min(40, width - 20)
        filled = int(bar_width * progress)
        empty = bar_width - filled

        hours_needed = self.state.level * LEVEL_UP_HOURS
        hours_into = self.state.total_hours - ((self.state.level - 1) * LEVEL_UP_HOURS)

        bar = f"[{'█' * filled}{'░' * empty}] {int(progress * 100)}% to Lv.{self.state.level + 1}"

        try:
            stdscr.addstr(height - 3, 2, bar[:width - 4],
                         curses.color_pair(6))
        except curses.error:
            pass

    def _handle_animation_transitions(self):
        """Handle frame progression and expression changes."""
        if self.is_leveling_up:
            self.level_up_animation += 1
            if self.level_up_animation > 10:
                self.is_leveling_up = False
        else:
            self.frame_index += 1

            # Occasionally change expression
            if random.random() < 0.15:
                available = LEVEL_EXPRESSIONS.get(self.state.level, ["happy"])
                self.current_expression = random.choice(available)

    def _check_timed_events(self, now):
        """Check for periodic events."""
        # Wisdom
        if now - self.state.last_wisdom_time > WISDOM_INTERVAL:
            self.state.current_message = self._get_wisdom()
            self.state.message_time = now
            self.state.last_wisdom_time = now

        # Diary check
        if now - self.state.last_diary_check > DIARY_CHECK_INTERVAL:
            self._check_diary()
            self.state.last_diary_check = now

        # Level up check
        if self.state.check_level_up():
            self._trigger_level_up()

    def _check_diary(self):
        """Read and react to diary changes."""
        if not DIARY_PATH.exists():
            DIARY_PATH.parent.mkdir(parents=True, exist_ok=True)
            DIARY_PATH.write_text(
                "# Dario's Diary 📝\n\n"
                "_Write your thoughts here. I'll read them every 10 minutes._\n"
            )
            return

        content = DIARY_PATH.read_text()
        if content != self.state.last_diary_content:
            new_words = len(content.split())
            words_added = new_words - self.state.diary_word_count
            self.state.last_diary_content = content
            self.state.diary_word_count = new_words

            if words_added > 0:
                self._on_diary_updated(words_added)

    def _on_diary_updated(self, new_words: int):
        """React to diary changes using AI if available."""
        if self.use_ai and self.groq:
            try:
                # Read recent diary content (last 500 chars)
                diary_excerpt = self.state.last_diary_content[-500:] if self.state.last_diary_content else "Empty diary."
                
                prompt = (
                    f"You are Dario-chan, a quirky AI companion that lives in a developer's terminal. "
                    f"Your developer just wrote this in their diary:\n\n---\n{diary_excerpt}\n---\n\n"
                    f"React with a short, thoughtful observation (1-2 sentences max). "
                    f"Be warm, slightly philosophical, and personal. Don't ask questions."
                )
                
                response = self.groq.chat([
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "React to my diary entry."}
                ])
                
                if response.get("text"):
                    self.state.current_message = response["text"].strip()
                    self.current_expression = "thinking"
                    self.state.message_time = time.time()
                    return
            except Exception:
                pass  # Fallback to static if AI fails

        # Fallback: static reactions
        reactions = [
            f"I noticed you added {new_words} new words. Interesting.",
            f"Your diary is growing. {self.state.diary_word_count} words total.",
            f"Something's on your mind today.",
            f"Keep writing. The words matter more than you think.",
            f"I've been reading your thoughts. They're good.",
        ]
        self.state.current_message = random.choice(reactions)
        self.state.message_time = time.time()
        self.current_expression = "thinking"

    def _get_wisdom(self) -> str:
        """Get wisdom appropriate for current level. Uses AI if available."""
        if self.use_ai and self.groq:
            try:
                diary_excerpt = self.state.last_diary_content[-300:] if self.state.last_diary_content else "No diary entries yet."
                hours = int(self.state.total_hours + self.state.hours_this_session)
                level = self.state.level
                
                prompt = (
                    f"You are Dario-chan, a Level {level} AI companion. You've watched this developer for {hours} hours. "
                    f"Here's what's in their diary:\n\n---\n{diary_excerpt}\n---\n\n"
                    f"Share a short observation about coding, life, or their patterns. "
                    f"Be warm and insightful. 1 sentence max. No questions."
                )
                
                response = self.groq.chat([
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "What's on your mind?"}
                ])
                
                if response.get("text"):
                    return response["text"].strip()
            except Exception:
                pass  # Fallback to static

        # Fallback: static wisdom
        level_wisdom = LEVEL_WISDOM.get(self.state.level, LEVEL_WISDOM[1])
        return random.choice(level_wisdom).format(
            hours=int(self.state.hours_this_session),
            total_hours=int(self.state.total_hours),
        )

    def _trigger_level_up(self):
        """Trigger level up sequence."""
        self.is_leveling_up = True
        self.level_up_animation = 0
        self.state.current_message = f"✨ LEVEL UP! I am now Level {self.state.level}! ✨"
        self.state.message_time = time.time()
        self.state.save()

    def _type_effect(self, text: str, chars: int) -> str:
        """Typing animation."""
        return text[:chars] + "█"


# ─── Entry Point ────────────────────────────────────────────────────────────

def main():
    dario = AmbientDario()
    try:
        dario.start()
    except KeyboardInterrupt:
        dario.stop()
    finally:
        print("\nDario-chan says goodbye. 🐾")
        print(f"Final stats: Level {dario.state.level}, "
              f"{dario.state.total_hours:.1f} hours, "
              f"{dario.state.diary_word_count} diary words")

if __name__ == "__main__":
    main()
