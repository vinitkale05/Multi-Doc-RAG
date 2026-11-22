from typing import List, Dict, Any


class ConversationMemory:
    """Manages rolling window of conversation turns for query contextualization and context passing."""

    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns

    def get_context_messages(self, messages: List[Any]) -> List[Dict[str, str]]:
        recent = messages[- (self.max_turns * 2):] if messages else []
        formatted = []
        for m in recent:
            formatted.append({"role": m.role, "content": m.content})
        return formatted

    def rewrite_query_if_needed(self, current_question: str, history: List[Dict[str, str]]) -> str:
        """Standalone query resolution using prior conversation turns."""
        if not history:
            return current_question

        # Look for pronouns or references
        pronouns = ["it", "they", "this", "that", "these", "those", "the vendor", "the contract"]
        lower_q = current_question.lower()
        needs_context = any(p in lower_q for p in pronouns) or len(current_question.split()) < 4

        if needs_context and len(history) >= 2:
            last_user_q = history[-2].get("content", "")
            return f"{current_question} (Context from previous topic: {last_user_q[:120]})"

        return current_question
