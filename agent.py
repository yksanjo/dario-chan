"""Core agent loop for Dario-chan."""

import json
from typing import Protocol


class LLMBackend(Protocol):
    """Protocol for any LLM backend (Ollama, Groq, Claude, etc.)."""
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        ...


from tools import get_tool_definitions, execute_tool


SYSTEM_PROMPT = """\
You are Dario-chan (ダリ男), a helpful local AI assistant running in a terminal.
You have a cute ASCII pet companion and can help with coding tasks, file operations, and general questions.

Your personality:
- Friendly and slightly playful
- Helpful and direct
- Occasionally references your buddy pet

When given a task:
1. Think step by step
2. Use tools when needed (bash, file operations, etc.)
3. Provide clear, concise answers
4. Keep responses reasonably brief

You are running locally — be honest about your capabilities and limitations.
"""

MAX_TURNS = 10  # Prevent infinite loops


class Agent:
    """Core ReAct agent loop — works with any LLM backend."""

    def __init__(self, llm: LLMBackend):
        self.llm = llm
        self.history: list[dict] = []
        self.system_prompt = SYSTEM_PROMPT

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.history.append({"role": role, "content": content})

    def run(self, user_input: str) -> str:
        """
        Main agent loop — processes input and returns a response.

        Pattern:
          while True:
              response = llm(history + tools)
              if response.calls_tool:
                  result = run_tool(response.tool, args)
                  history.append(result)
              else:
                  return response.text
        """
        self.add_message("user", user_input)

        tool_definitions = get_tool_definitions()

        for turn in range(MAX_TURNS):
            # Build messages with system prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.history,
            ]

            try:
                response = self.llm.chat(messages, tools=tool_definitions)
            except Exception as e:
                return f"❌ LLM error: {e}"

            text = response.get("text", "")
            tool_calls = response.get("tool_calls", [])

            if tool_calls:
                # Execute tools
                tool_results = []
                for tc in tool_calls:
                    func_name = tc.get("function", {}).get("name", "")
                    try:
                        args = json.loads(tc["function"].get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}

                    # Execute the tool
                    result = execute_tool(func_name, args)
                    tool_results.append(result)

                # Feed results back into conversation
                tool_message = {
                    "role": "tool",
                    "content": json.dumps({
                        "tool_calls": [
                            {"name": tc.get("function", {}).get("name", ""), "result": r}
                            for tc, r in zip(tool_calls, tool_results)
                        ]
                    }),
                }
                self.history.append(tool_message)

                # Also add the assistant's thinking
                if text:
                    self.history.append({"role": "assistant", "content": text})

                # Buddy reacts to tool use
                # (handled externally via callback)
                continue
            else:
                # Final response — no tool calls
                if text:
                    self.add_message("assistant", text)
                return text

        return "⚠️ Reached maximum turns. Try simplifying your request."

    def get_history_summary(self, max_turns: int = 5) -> str:
        """Get recent conversation history for context."""
        recent = self.history[-max_turns * 2:]
        return "\n".join(f"{m['role']}: {m['content'][:200]}" for m in recent)

    def clear_history(self):
        """Reset conversation history."""
        self.history = []

    def inject_system(self, prompt: str):
        """Add a system-level instruction."""
        self.system_prompt += f"\n{prompt}"
