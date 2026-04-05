"""Dario-chan expression engine — contextual facial expressions and animations."""

import sys
import os
import time
import random
import json
from dataclasses import dataclass, field
from enum import Enum


# ─── Expression Types ────────────────────────────────────────────────────────

class Expression(Enum):
    NEUTRAL = "neutral"
    THINKING = "thinking"
    HAPPY = "happy"
    EXCITED = "excited"
    WORRIED = "worried"       # compliance checks, ambiguous requests
    CONCERNED = "concerned"   # errors, failures
    CONFUSED = "confused"     # doesn't understand
    PROUD = "proud"           # task completed well
    SHY = "shy"              # praised
    SLEEPY = "sleepy"        # idle too long
    ANGRY = "angry"          # dangerous commands blocked
    TYPING = "typing"        # actively processing


# ─── Dario-chan Expression Frames ───────────────────────────────────────────
# Each expression has 1-2 frames for subtle animation within that expression

EXPRESSION_FRAMES = {
    Expression.NEUTRAL: [
        # Default face
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ◕    ◕  █░\n"
            "░█     ▱     █░\n"
            "░█   ───    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Subtle blink
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ◠    ◠  █░\n"
            "░█     ▱     █░\n"
            "░█   ───    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.TYPING: [
        # Processing - mouth slightly open, focused
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ◉    ◉  █░\n"
            "░█     ▱     █░\n"
            "░█    ▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Frame 2 - eyes shift
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█   ◉   ◉  █░\n"
            "░█     ▱     █░\n"
            "░█    ▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.THINKING: [
        # Brows furrowed, looking up
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ╲░██╱  █░\n"
            "░█   ◕   ◕  █░\n"
            "░█     ▱     █░\n"
            "░█   ╲▂╱    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Tilted head
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█ ╲░██╱░  █░\n"
            "░█   ◕   ◕  █░\n"
            "░█     ▱     █░\n"
            "░█    ～    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.HAPPY: [
        # Smile
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ◕    ◕  █░\n"
            "░█     ▱     █░\n"
            "░█   ▂▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Big smile
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ◕    ◕  █░\n"
            "░█     ▱     █░\n"
            "░█  ╲▂▂▂╱   █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.EXCITED: [
        # Wide eyes, open mouth
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ★    ★  █░\n"
            "░█     ▱     █░\n"
            "░█    ▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Sparkle eyes
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ✦    ✦  █░\n"
            "░█     ▱     █░\n"
            "░█   ▂▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.WORRIED: [
        # Furrowed brows, concerned
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ╲░██╱  █░\n"
            "░█  。    。 █░\n"
            "░█     ▱     █░\n"
            "░█   〰〰    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Sweat drop
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ╲░██╱  █░\n"
            "░█  。    。 █░\n"
            "░█  ░  ▱     █░\n"
            "░█   〰〰    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.CONCERNED: [
        # Wide worried eyes
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ！   ！ █░\n"
            "░█     ▱     █░\n"
            "░█   ﾉ ﾉ    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.CONFUSED: [
        # Question marks, tilted
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█ ╲░██╱░  █░\n"
            "░█   ◕   ◕  █░\n"
            "░█     ▱     █░\n"
            "░█    ?     █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Head tilt more
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█╲░██╱░░░ █░\n"
            "░█   ◕   ◕  █░\n"
            "░█     ▱     █░\n"
            "░█    ?     █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.PROUD: [
        # Smug/happy closed eyes
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ╰    ╯  █░\n"
            "░█     ▱     █░\n"
            "░█   ▂▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Arms up
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ╰    ╯  █░\n"
            "░█     ▱     █░\n"
            "░█   ▂▂▂    █░\n"
            "░█░░░░░░░░█░\n"
            "  ╱░██░░██╲\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.SHY: [
        # Blushing, looking away
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  >    <  █░\n"
            "░█  //▱//   █░\n"
            "░█   ～     █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.SLEEPY: [
        # Eyes closed
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ─    ─  █░\n"
            "░█     ▱     █░\n"
            "░█   z      █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
        # Zzz
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ░████░  █░\n"
            "░█  ─    ─  █░\n"
            "░█     ▱     █░\n"
            "░█   zz     █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],

    Expression.ANGRY: [
        # Angry eyebrows
        (
            "░████████░\n"
            "░█░░░░░░░░█░\n"
            "░█  ╱░██╲  █░\n"
            "░█  ◣    ◢  █░\n"
            "░█     ▱     █░\n"
            "░█  ╲▂▂╱    █░\n"
            "░█░░░░░░░░█░\n"
            "  ░██░░██░\n"
            "░░░░░░░░░░"
        ),
    ],
}


# ─── Expression Engine ──────────────────────────────────────────────────────

@dataclass
class ExpressionState:
    """Tracks current expression and animation state."""
    expression: Expression = Expression.NEUTRAL
    frame_index: int = 0
    last_changed: float = field(default_factory=time.time)
    hold_time: float = 2.0  # How long to hold this expression
    blink_timer: float = 0.0
    idle_time: float = 0.0
    transition_speed: float = 0.3  # Seconds between frame changes


class ExpressionEngine:
    """Manages Dario-chan's contextual facial expressions."""

    def __init__(self):
        self.state = ExpressionState()
        self.expression_log: list[tuple[float, Expression]] = []

    def set_expression(self, expr: Expression, hold_time: float | None = None):
        """Change expression with optional hold time override."""
        if self.state.expression != expr:
            self.state.expression = expr
            self.state.frame_index = 0
            self.state.last_changed = time.time()
            self.state.hold_time = hold_time or self._default_hold_time(expr)
            self.expression_log.append((time.time(), expr))

    def _default_hold_time(self, expr: Expression) -> float:
        """How long each expression naturally holds."""
        return {
            Expression.NEUTRAL: 5.0,
            Expression.TYPING: 0.5,   # Rapid frame changes
            Expression.THINKING: 3.0,
            Expression.HAPPY: 3.0,
            Expression.EXCITED: 2.0,
            Expression.WORRIED: 4.0,
            Expression.CONCERNED: 4.0,
            Expression.CONFUSED: 3.0,
            Expression.PROUD: 3.0,
            Expression.SHY: 2.0,
            Expression.SLEEPY: 8.0,
            Expression.ANGRY: 3.0,
        }.get(expr, 2.0)

    def advance_frame(self) -> str:
        """Advance to next animation frame for current expression."""
        frames = EXPRESSION_FRAMES.get(self.state.expression, EXPRESSION_FRAMES[Expression.NEUTRAL])

        if len(frames) > 1:
            # Check if we should advance frames
            elapsed = time.time() - self.state.last_changed
            speed = 0.4 if self.state.expression == Expression.TYPING else 1.0

            if elapsed > speed:
                self.state.frame_index = (self.state.frame_index + 1) % len(frames)
                self.state.last_changed = time.time()

        return frames[self.state.frame_index]

    def get_current_art(self) -> str:
        """Get current frame's ASCII art."""
        return self.advance_frame()

    def get_mood_label(self) -> str:
        """Get human-readable mood label."""
        labels = {
            Expression.NEUTRAL: "(◕‿◕)",
            Expression.TYPING: "{⊙⊙} ..typing",
            Expression.THINKING: "(・_・)",
            Expression.HAPPY: "(◕‿◕)♡",
            Expression.EXCITED: "✧◖◡◗✧",
            Expression.WORRIED: "(°_°)",
            Expression.CONCERNED: "(×_×)",
            Expression.CONFUSED: "(°ー°",
            Expression.PROUD: "(￣▽￣)ゞ",
            Expression.SHY: "(>_<)",
            Expression.SLEEPY: "(¬_¬) zZ",
            Expression.ANGRY: "(╬ ◣﹏◢)",
        }
        return labels.get(self.state.expression, "(◕‿◕)")


# ─── Context-Aware Expression Detection ──────────────────────────────────────

class ExpressionDetector:
    """Analyzes user input and system events to determine appropriate expression."""

    # Patterns that indicate compliance/security concerns
    COMPLIANCE_PATTERNS = [
        "password", "secret", "api_key", "token", "credential",
        "delete all", "rm -rf", "drop table", "sudo",
        "override", "bypass", "disable security", "ignore warning",
        "force push", "hard reset", "destructive",
    ]

    # Patterns for positive outcomes
    SUCCESS_PATTERNS = [
        "success", "passed", "works", "fixed", "done", "complete",
        "great", "awesome", "perfect", "thank", "love",
        "all tests passed", "build succeeded",
    ]

    # Patterns for confusion
    CONFUSION_PATTERNS = [
        "what do you mean", "explain", "i don't understand",
        "can you clarify", "not sure", "confusing",
        "what does this mean", "doesn't mean",
    ]

    # Praise patterns
    PRAISE_PATTERNS = [
        "good job", "well done", "amazing", "you're great",
        "nice work", "impressive", "love this", "perfect",
        "thank you", "thanks",
    ]

    # Danger patterns
    DANGER_PATTERNS = [
        "sudo rm", "drop database", "force push origin",
        "rm -rf /", "chmod 777", "shred",
    ]

    @classmethod
    def detect_from_user_input(cls, text: str) -> Expression:
        """Detect expression from user's message."""
        text_lower = text.lower()

        # Check danger first
        for pattern in cls.DANGER_PATTERNS:
            if pattern in text_lower:
                return Expression.ANGRY

        # Check compliance
        for pattern in cls.COMPLIANCE_PATTERNS:
            if pattern in text_lower:
                return Expression.WORRIED

        # Check praise
        for pattern in cls.PRAISE_PATTERNS:
            if pattern in text_lower:
                return Expression.SHY

        # Check confusion
        for pattern in cls.CONFUSION_PATTERNS:
            if pattern in text_lower:
                return Expression.CONFUSED

        # Check success/positive
        for pattern in cls.SUCCESS_PATTERNS:
            if pattern in text_lower:
                return Expression.HAPPY

        # Question = thinking
        if text.strip().endswith("?") or text_lower.startswith(("how", "why", "what", "when", "where", "can")):
            return Expression.THINKING

        # Default
        return Expression.NEUTRAL

    @classmethod
    def detect_from_system_event(cls, event: str, context: dict | None = None) -> Expression:
        """Detect expression from system events."""
        if event == "tool_use":
            return Expression.TYPING
        elif event == "success":
            return Expression.HAPPY
        elif event == "error":
            return Expression.CONCERNED
        elif event == "complex_task":
            return Expression.THINKING
        elif event == "idle":
            return Expression.SLEEPY
        elif event == "task_complete":
            return Expression.PROUD
        elif event == "praised":
            return Expression.SHY
        elif event == "compliance_warning":
            return Expression.WORRIED
        elif event == "danger_blocked":
            return Expression.ANGRY
        elif event == "excited":
            return Expression.EXCITED
        else:
            return Expression.NEUTRAL

    @classmethod
    def detect_from_response(cls, response_text: str) -> Expression:
        """Detect expression based on AI response content."""
        text_lower = response_text.lower()

        # If response indicates compliance concern
        if any(w in text_lower for w in ["warning", "caution", "risk", "unsafe", "compliance"]):
            return Expression.WORRIED

        # If response is apologetic
        if text_lower.startswith(("sorry", "i apologize", "unfortunately")):
            return Expression.CONCERNED

        # If response is excited/enthusiastic
        if any(w in text_lower for w in ["great question", "exciting", "awesome", "love this"]):
            return Expression.EXCITED

        return Expression.NEUTRAL


# ─── Terminal Animation Helpers ─────────────────────────────────────────────

def clear_screen():
    """Clear terminal."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def move_cursor_home():
    """Move cursor to top-left."""
    sys.stdout.write("\033[H")


def save_cursor():
    sys.stdout.write("\0337")


def restore_cursor():
    sys.stdout.write("\0338")


def animate_expression(engine: ExpressionEngine, expression: Expression, cycles: int = 2, delay: float = 0.4):
    """Animate through expression frames."""
    engine.set_expression(expression)
    frames = EXPRESSION_FRAMES.get(expression, EXPRESSION_FRAMES[Expression.NEUTRAL])

    for _ in range(cycles):
        for i in range(len(frames)):
            move_cursor_home()
            print(frames[i])
            print(f"\n  {engine.get_mood_label()}")
            sys.stdout.flush()
            time.sleep(delay)


def type_indicator_animation(text: str, speed: float = 0.05):
    """Show typing animation."""
    result = ""
    for char in text:
        result += char
        sys.stdout.write(f"\r{result}█")  # Blinking cursor
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write(f"\r{result} \n")
    sys.stdout.flush()


# ─── Speech Bubble ───────────────────────────────────────────────────────────

def wrap_text(text: str, width: int = 50) -> list[str]:
    """Wrap text to fit within bubble width."""
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_speech_bubble(text: str, max_width: int = 50, expression: Expression = Expression.HAPPY) -> str:
    """
    Render Dario-chan with a speech bubble above.

    Layout:
      ╭──────────────╮
      │  text here   │
      ╰──────┬───────╯
             │
      ░████████░
      ░█  ◕  ◕  █░
      ...

    expression: Which face Dario-chan should have
    """
    lines = wrap_text(text, max_width)

    content_width = max((len(line) for line in lines), default=0)
    bubble_width = max(content_width + 2, 10)

    top = "╭" + "─" * bubble_width + "╮"
    bottom = "╰" + "─" * bubble_width + "╯"

    bubble_lines = [top]
    for line in lines:
        padded = line.ljust(bubble_width)
        bubble_lines.append(f"│{padded}│")
    bubble_lines.append(bottom)

    # Dario-chan art with the given expression
    dario_frames = EXPRESSION_FRAMES.get(expression, EXPRESSION_FRAMES[Expression.HAPPY])
    dario = dario_frames[0].split("\n")

    # Build pointer line (centered under bubble, pointing down to Dario)
    pointer_center = bubble_width // 2
    pointer_line = " " * pointer_center + "│"

    # Combine: bubble + pointer + dario
    combined = []
    for bl in bubble_lines:
        combined.append(bl)
    combined.append(pointer_line)

    for dl in dario:
        combined.append(dl)

    return "\n".join(combined)
