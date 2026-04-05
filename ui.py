"""Split-terminal UI — Dario-chan panel + conversation panel."""

import sys
import os
import time


class TerminalUI:
    """
    Split terminal layout:

    ╔══════════════════════════════════════════════╗
    ║            DARIO-CHAN PANEL                   ║
    ║  (Expression art + speech bubble)             ║
    ╚══════════════════════════════════════════════╝
    ────────────────────────────────────────────────
    ╔══════════════════════════════════════════════╗
    ║  Conversation history (scrollable)            ║
    ║  ┌─────────────────────────────────────────┐ ║
    ║  │ user: what is this?                      │ ║
    ║  │ dari: Let me help...                     │ ║
    ║  └─────────────────────────────────────────┘ ║
    ║  (◕‿◕) > _                                   ║
    ╚══════════════════════════════════════════════╝
    """

    # Layout constants
    DARIO_PANEL_HEIGHT = 14  # Lines reserved for Dario-chan
    MARGIN = 1

    def __init__(self, term_width: int | None = None, term_height: int | None = None):
        try:
            cols, rows = os.get_terminal_size()
        except OSError:
            cols, rows = 80, 24  # Default fallback
        self.width = term_width or cols
        self.height = term_height or rows
        self.conversation: list[tuple[str, str]] = []  # (speaker, text)
        self.scroll_offset = 0

    def setup(self):
        """Initialize the terminal for split layout."""
        # Hide cursor, enable alternate screen
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.write("\033[?1049h")  # Alternate screen buffer
        sys.stdout.flush()

    def teardown(self):
        """Restore terminal to normal."""
        sys.stdout.write("\033[?25h")  # Show cursor
        sys.stdout.write("\033[?1049l")  # Normal screen buffer
        sys.stdout.flush()

    def draw_dario_panel(self, art: str, bubble: str | None = None, mood: str = ""):
        """Draw the top Dario-chan panel."""
        # Move to top-left
        sys.stdout.write(f"\033[1;1H")

        # Panel border
        border_char = "═"
        sys.stdout.write(f"\033[1;1H╔{border_char * (self.width - 2)}╗\n")
        sys.stdout.write(f"║{'DARIO-CHAN':^{self.width - 2}}║\n")

        # Content area
        content_start = 3
        if bubble:
            bubble_lines = bubble.split("\n")
            for i, line in enumerate(bubble_lines):
                if content_start + i >= self.DARIO_PANEL_HEIGHT:
                    break
                padded = f" {line}".ljust(self.width - 2)[:self.width - 2]
                sys.stdout.write(f"║{padded}║\n")
        elif art:
            art_lines = art.split("\n")
            for i, line in enumerate(art_lines):
                if content_start + i >= self.DARIO_PANEL_HEIGHT:
                    break
                padded = f" {line}".ljust(self.width - 2)[:self.width - 2]
                sys.stdout.write(f"║{padded}║\n")

        # Mood line
        if mood:
            sys.stdout.write(f"║{'':>{self.width - len(mood) - 2}}{mood} ║\n")

        # Fill remaining lines
        lines_used = content_start + (len(bubble.split("\n")) if bubble else 0)
        remaining = self.DARIO_PANEL_HEIGHT - lines_used - 1
        for _ in range(max(0, remaining)):
            sys.stdout.write(f"║{' ' * (self.width - 2)}║\n")

        # Bottom border
        sys.stdout.write(f"╚{'═' * (self.width - 2)}╝\n")
        sys.stdout.flush()

    def draw_conversation(self, max_lines: int | None = None):
        """Draw the conversation history area."""
        # Position cursor after Dario panel
        start_line = self.DARIO_PANEL_HEIGHT + 2
        sys.stdout.write(f"\033[{start_line};1H")

        # Separator
        sys.stdout.write(f"{'─' * self.width}\n")

        # Calculate available lines
        available = self.height - start_line - 2  # minus separator + input line + prompt
        if max_lines:
            available = min(available, max_lines)

        # Show most recent messages
        visible = self.conversation[-available:]

        for speaker, text in visible:
            if speaker == "user":
                prefix = "  (◕‿◕) > "
                sys.stdout.write(f"\033[36m{prefix}{text}\033[0m\n")
            else:
                prefix = "  ダリ男> "
                sys.stdout.write(f"\033[33m{prefix}{text}\033[0m\n")

        sys.stdout.flush()

    def draw_prompt(self, mood: str = "(◕‿◕)"):
        """Draw the input prompt at bottom."""
        # Move to bottom
        sys.stdout.write(f"\033[{self.height};1H")
        sys.stdout.write(f"  {mood} > ")
        sys.stdout.flush()

    def redraw_all(self, dario_art: str = "", bubble: str | None = None, mood: str = ""):
        """Full redraw of everything."""
        self.draw_dario_panel(dario_art, bubble, mood)
        self.draw_conversation()
        self.draw_prompt(mood)

    def add_message(self, speaker: str, text: str):
        """Add a message to conversation history."""
        self.conversation.append((speaker, text))
        # Keep history manageable
        if len(self.conversation) > 100:
            self.conversation = self.conversation[-80:]

    def get_input(self) -> str:
        """Get user input (blocking)."""
        try:
            return input()
        except EOFError:
            return "/quit"
        except KeyboardInterrupt:
            return ""

    def clear(self):
        """Clear conversation history."""
        self.conversation.clear()
        self.scroll_offset = 0
