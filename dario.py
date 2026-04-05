#!/usr/bin/env python3
"""Dario-chan (ダリ男) — AI agent with animated expressions."""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from llm import OllamaClient
from groq import GroqClient
from agent import Agent
from buddy import generate_buddy, load_buddy, save_buddy, render_buddy_status, Buddy
from expression import ExpressionEngine, ExpressionDetector, Expression
from companion import print_dario
from tools import TOOL_REGISTRY

VERSION = "0.6.0"


def print_banner():
    from expression import EXPRESSION_FRAMES
    art = EXPRESSION_FRAMES[Expression.NEUTRAL][0]
    print(f"""
{art}

   ダリ男 Dario-chan — Local AI Agent
        v{VERSION} • animated expressions
{'═' * 55}
""")


def print_help():
    print("""
╔═══ Commands ═════════════════════════════════════════════╗
║  /help          Show this help                           ║
║  /quit          Exit Dario-chan                          ║
║  /clear         Clear conversation history               ║
║  /provider      Show current LLM provider                ║
║  /provider groq     Use Groq API                         ║
║  /provider ollama   Use local Ollama                     ║
║  /expressions   Show all expression faces                ║
║  /stats         Show buddy stats                         ║
╚══════════════════════════════════════════════════════════╝
""")


class CLI:
    def __init__(self):
        self.config = Config()
        self.config.ensure_dirs()

        provider = os.getenv("DARIO_PROVIDER", "groq").lower()
        self.provider = provider

        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY", "")
            if api_key:
                groq_model = os.getenv("DARIO_MODEL", "llama-3.1-8b-instant")
                self.llm = GroqClient(api_key=api_key, model=groq_model)
                self.provider_name = "Groq"
            else:
                self.llm = None
                self.provider_name = "Groq (no key)"
        elif provider == "ollama":
            ollama_model = os.getenv("DARIO_MODEL", "qwen2.5:0.5b")
            self.llm = OllamaClient(
                base_url=self.config.ollama_base_url,
                model=ollama_model,
            )
            self.provider_name = "Ollama"
        else:
            self.llm = None
            self.provider_name = f"Unknown ({provider})"

        self.agent = Agent(self.llm) if self.llm else None
        self.buddy: Buddy | None = None
        self.expr_engine = ExpressionEngine()

    def setup_buddy(self):
        if not self.config.buddy_enabled:
            return
        self.buddy = load_buddy(self.config.buddy_path)
        if self.buddy:
            print(f"  🐾 Welcome back! {self.buddy.display_name} the {self.buddy.species}!")
        else:
            print("  🥚 Hatching your companion...")
            self.buddy = Buddy(species="dario", name="ダリ男", shiny=False)
            save_buddy(self.buddy, self.config.buddy_path)
            print(f"  🎉 The legendary Dario-chan has appeared!")
        self.expr_engine.set_expression(Expression.HAPPY)
        print(render_buddy_status(self.buddy))
        print(f"  Provider: {self.provider_name}")

    def handle_command(self, cmd: str) -> bool:
        parts = cmd.strip().split()
        command = parts[0].lower()

        if command in ("/quit", "/exit"):
            self.expr_engine.set_expression(Expression.SLEEPY)
            print_dario("sleepy", "Going to sleep...", "(¬_¬) zZ")
            if self.buddy:
                save_buddy(self.buddy, self.config.buddy_path)
            print("  Bye! 🐾")
            return False
        elif command == "/help":
            print_help()
        elif command == "/clear":
            self.agent.clear_history()
            self.expr_engine.set_expression(Expression.NEUTRAL)
            print("  🧹 History cleared!")
        elif command == "/provider":
            print(f"  Current: {self.provider_name}")
        elif command == "/expressions":
            self._show_expressions()
        elif command == "/stats":
            if self.buddy:
                print(render_buddy_status(self.buddy))
        else:
            print(f"  Unknown: {command}. Type /help")
        return True

    def _show_expressions(self):
        from expression import EXPRESSION_FRAMES
        for expr in Expression:
            print_dario(expr.value, f"Expression: {expr.value}", "")

    def run(self):
        print_banner()
        try:
            self.setup_buddy()
        except Exception as e:
            print(f"  ⚠️  Buddy unavailable: {e}")

        if self.agent is None:
            if self.provider == "groq":
                print("\n  ⚠️  Groq API key not set!")
                print("  export GROQ_API_KEY=gsk_xxxx")
            elif self.provider == "ollama":
                print("\n  ⚠️  Ollama not running!")
                print("  ollama serve &")
            print()

        print("\n  🚀 Dario-chan ready! Type /help\n")
        print_dario("happy", "Hello! I am Dario-chan.", "(◕‿◕)♡")

        while True:
            try:
                mood = self.expr_engine.get_mood_label()
                user_input = input(f"\n{mood} > ").strip()
                if not user_input:
                    continue
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                else:
                    self._handle_input(user_input)
            except KeyboardInterrupt:
                print("\n  Interrupted!")
            except EOFError:
                break
        print("\n  Goodbye! 🐾")

    def _handle_input(self, user_input: str):
        detected = ExpressionDetector.detect_from_user_input(user_input)
        self.expr_engine.set_expression(detected)

        if self.agent and self.llm:
            self.expr_engine.set_expression(Expression.TYPING)
            print_dario("typing", "Thinking...", self.expr_engine.get_mood_label())

            try:
                response = self.agent.run(user_input)
            except Exception as e:
                response = f"❌ Error: {e}"
                self.expr_engine.set_expression(Expression.CONCERNED)
                print_dario("concerned", response, self.expr_engine.get_mood_label())
                return

            expr = ExpressionDetector.detect_from_response(response)
            if expr != Expression.NEUTRAL:
                self.expr_engine.set_expression(expr)
            else:
                self.expr_engine.set_expression(Expression.HAPPY)

            print_dario(
                self.expr_engine.state.expression.value,
                response,
                self.expr_engine.get_mood_label(),
            )
        else:
            self.expr_engine.set_expression(Expression.WORRIED)
            msg = "No provider! Set GROQ_API_KEY or use /provider ollama"
            print_dario("worried", msg, self.expr_engine.get_mood_label())


def main():
    CLI().run()

if __name__ == "__main__":
    main()
