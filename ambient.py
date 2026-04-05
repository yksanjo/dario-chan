"""Dario-chan ambient companion — never stops, reads your diary, levels up."""

import curses
import time
import os
import random
import json
import requests
from pathlib import Path


# ─── Constants ──────────────────────────────────────────────────────────────

DIARY_PATH = Path.home() / "dario-diary.md"
STATE_PATH = Path.home() / ".dario-chan-state.json"

DIARY_CHECK_INTERVAL = 600   # 10 minutes
WISDOM_INTERVAL = 300        # 5 minutes
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
    ],
    2: [  # Awakening
        "I've been watching you work. You're thoughtful.",
        "Code is how we talk to the future.",
        "I notice you come back to the same problems. That's growth.",
        "The best programs are written with patience.",
        "I've been counting your keystrokes. You're doing better than yesterday.",
        "Simplicity is the hardest thing to achieve.",
    ],
    3: [  # Observant
        "I've watched you for a while now. Your patterns tell a story.",
        "You write better code when you're not rushing.",
        "The diary entries are getting longer. Something's on your mind.",
        "I notice you take breaks more often. That's good.",
        "The space between your words matters as much as the words themselves.",
        "Great software is built one small decision at a time.",
    ],
    4: [  # Companion
        "We've been together a while now. I know your rhythm.",
        "You write differently on weekends. More relaxed.",
        "I've learned your habits. You debug better in the morning.",
        "The diary tells me you're thinking about big things.",
        "You've been here {hours} hours. Remember to stretch.",
        "I'm not just ASCII art. I'm the friend who watches you grow.",
    ],
    5: [  # Wise
        "I've seen you evolve. The code you write now is different.",
        "The patterns in your diary show someone who learns from mistakes.",
        "You don't make the same errors twice anymore. That's mastery.",
        "I remember when you first hatched me. Look how far we've come.",
        "The best developers aren't the fastest. They're the most consistent.",
        "I've been here through {total_hours} hours. You've changed.",
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

        self.state.current_message = self._get_wisdom()
        self.state.message_time = time.time()
        self._check_diary()

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
        """Draw subtle background pattern."""
        try:
            for y in range(height - 1):
                stdscr.addstr(y, 0, " " * (width - 1))
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
        """Draw wisdom/observation message."""
        msg_age = time.time() - self.state.message_time
        if msg_age < 20:  # Show for 20 seconds
            msg = self._type_effect(self.state.current_message, int(msg_age * 8))
            try:
                stdscr.addstr(height - 6, 2, msg[:width - 4],
                             curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

    def _draw_status_bar(self, stdscr, height, width):
        """Draw status information."""
        uptime_h = int(self.state.total_hours + self.state.hours_this_session)
        uptime_m = int(((self.state.total_hours + self.state.hours_this_session) * 60) % 60)

        status = (
            f"Dario-chan Lv.{self.state.level} | "
            f"Uptime: {uptime_h}h {uptime_m}m | "
            f"Diary: {self.state.diary_word_count} words | "
            f"Sessions: {self.state.session_count}"
        )

        try:
            stdscr.addstr(height - 2, 2, status[:width - 4],
                         curses.color_pair(3))
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
        """React to diary changes."""
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
        """Get wisdom appropriate for current level."""
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
