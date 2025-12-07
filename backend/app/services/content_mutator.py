"""
Content Mutator for the Ritual Engine.
Corrupts and transforms text content based on user progress.
"""

import random
import re
from typing import Optional, List
from datetime import datetime

from app.schemas.ritual import RitualState
from app.services.progress_engine import ProgressEngine, ProgressLevel


class ContentMutator:
    """
    Corrupts and transforms content based on user's ritual progress.

    Corruption types:
    - Glitch characters: Replace chars with block/glitch symbols
    - Zalgo: Add combining diacritics for "cursed" text effect
    - Word replacement: Replace words with creepy alternatives
    - Insertion: Insert creepy messages into text
    - Redaction: Black out words with █

    Usage:
        mutator = ContentMutator()

        # Check if should corrupt
        if mutator.should_corrupt(state):
            corrupted = mutator.corrupt_text(text, state.progress / 100)

        # Mutate entire post
        mutated_post = mutator.mutate_post(post_dict, state)
    """

    # Glitch/corruption characters
    GLITCH_CHARS = "░▒▓█▄▀■□▪▫●○◆◇"
    ZALGO_CHARS = [
        '\u0300', '\u0301', '\u0302', '\u0303', '\u0304', '\u0305',
        '\u0306', '\u0307', '\u0308', '\u0309', '\u030A', '\u030B',
        '\u030C', '\u030D', '\u030E', '\u030F', '\u0310', '\u0311',
        '\u0312', '\u0313', '\u0314', '\u0315', '\u0316', '\u0317',
        '\u0318', '\u0319', '\u031A', '\u031B', '\u031C', '\u031D',
    ]

    # Creepy word replacements
    WORD_REPLACEMENTS = {
        "привет": ["...привет..."],
        "здравствуй": ["они здесь"],
        "помощь": ["помоги мне"],
        "ответ": ["они слышат"],
        "время": ["время истекает"],
        "друг": ["ты не один"],
        "один": ["никогда не один"],
        "темно": ["они в темноте"],
        "свет": ["свет гаснет"],
        "дом": ["дом помнит"],
        "ночь": ["ночь видит"],
    }

    # Insertable creepy phrases
    CREEPY_INSERTIONS = [
        "...",
        "ОНИ ЗДЕСЬ",
        "НЕ ОГЛЯДЫВАЙСЯ",
        "ПОМОГИ",
        "Я ВИЖУ ТЕБЯ",
        "ТЫ НЕ ОДИН",
        "СКОРО",
        "МЫ ЖДЁМ",
        "ОН СМОТРИТ",
        "БЕГИ",
    ]

    # Meta messages that reference the reader
    META_MESSAGES = [
        "Ты ещё здесь?",
        "Зачем ты читаешь это?",
        "Мы знаем, что ты смотришь.",
        "Ты чувствуешь это?",
        "Не закрывай страницу.",
    ]

    def __init__(self):
        self.progress_engine = ProgressEngine()

    def should_corrupt(self, state: RitualState) -> bool:
        """Check if content should be corrupted for this user."""
        chance = self.progress_engine.get_corruption_chance(state)
        return random.random() < chance

    def get_corruption_intensity(self, state: RitualState) -> float:
        """Get corruption intensity (0.0 - 1.0)."""
        return self.progress_engine.get_corruption_intensity(state)

    def corrupt_text(
        self,
        text: str,
        intensity: float = 0.3,
        style: Optional[str] = None,
    ) -> str:
        """
        Corrupt text with various effects.

        Args:
            text: Original text
            intensity: Corruption intensity (0.0 - 1.0)
            style: Optional corruption style (glitch, zalgo, redact, insert)
                   If None, randomly selects based on intensity

        Returns:
            Corrupted text
        """
        if not text or intensity <= 0:
            return text

        intensity = min(1.0, max(0.0, intensity))

        # Select style based on intensity if not specified
        if style is None:
            if intensity < 0.3:
                style = random.choice(["glitch", "insert"])
            elif intensity < 0.6:
                style = random.choice(["glitch", "zalgo", "replace", "insert"])
            else:
                style = random.choice(["glitch", "zalgo", "redact", "replace"])

        if style == "glitch":
            return self._apply_glitch(text, intensity)
        elif style == "zalgo":
            return self._apply_zalgo(text, intensity)
        elif style == "redact":
            return self._apply_redaction(text, intensity)
        elif style == "replace":
            return self._apply_word_replacement(text)
        elif style == "insert":
            return self._apply_insertion(text, intensity)
        else:
            return self._apply_glitch(text, intensity)

    def _apply_glitch(self, text: str, intensity: float) -> str:
        """Replace random characters with glitch symbols."""
        chars = list(text)
        num_glitches = int(len(chars) * intensity * 0.3)

        for _ in range(num_glitches):
            if chars:
                idx = random.randint(0, len(chars) - 1)
                if chars[idx].isalnum():
                    chars[idx] = random.choice(self.GLITCH_CHARS)

        return "".join(chars)

    def _apply_zalgo(self, text: str, intensity: float) -> str:
        """Add zalgo/combining characters for cursed effect."""
        result = []
        marks_per_char = int(1 + intensity * 3)

        for char in text:
            result.append(char)
            if char.isalnum() and random.random() < intensity:
                for _ in range(marks_per_char):
                    result.append(random.choice(self.ZALGO_CHARS))

        return "".join(result)

    def _apply_redaction(self, text: str, intensity: float) -> str:
        """Black out random words."""
        words = text.split()
        num_redact = int(len(words) * intensity * 0.4)

        indices = random.sample(range(len(words)), min(num_redact, len(words)))
        for idx in indices:
            word_len = len(words[idx])
            words[idx] = "█" * word_len

        return " ".join(words)

    def _apply_word_replacement(self, text: str) -> str:
        """Replace specific words with creepy alternatives."""
        result = text.lower()
        for word, replacements in self.WORD_REPLACEMENTS.items():
            if word in result:
                result = result.replace(word, random.choice(replacements), 1)
        return result

    def _apply_insertion(self, text: str, intensity: float) -> str:
        """Insert creepy phrases into text."""
        if random.random() > intensity:
            return text

        insertion = random.choice(self.CREEPY_INSERTIONS)

        # Insert at random position
        words = text.split()
        if len(words) > 3:
            pos = random.randint(1, len(words) - 1)
            words.insert(pos, f"\n{insertion}\n")

        return " ".join(words)

    def mutate_post(
        self,
        post_data: dict,
        state: RitualState,
    ) -> dict:
        """
        Apply mutations to a post based on user state.

        Args:
            post_data: Post data dictionary
            state: User's RitualState

        Returns:
            Mutated post data (original is not modified)
        """
        # Create copy to avoid modifying original
        result = dict(post_data)

        # Check if should corrupt
        if not self.should_corrupt(state):
            return result

        intensity = self.get_corruption_intensity(state)

        # Corrupt content
        if "content" in result and result["content"]:
            result["content"] = self.corrupt_text(
                result["content"], intensity
            )
            result["_corrupted"] = True

        # Maybe add meta information
        level = self.progress_engine.get_level_from_state(state)
        if level in [ProgressLevel.HIGH, ProgressLevel.CRITICAL]:
            if random.random() < 0.3:
                result["_meta_message"] = random.choice(self.META_MESSAGES)

        # At critical level, might show "edited" timestamp that changes
        if level == ProgressLevel.CRITICAL and random.random() < 0.2:
            result["_fake_edit"] = datetime.utcnow().isoformat()

        return result

    def mutate_thread(
        self,
        thread_data: dict,
        state: RitualState,
    ) -> dict:
        """
        Apply mutations to a thread.

        Args:
            thread_data: Thread data dictionary
            state: User's RitualState

        Returns:
            Mutated thread data
        """
        result = dict(thread_data)

        if not self.should_corrupt(state):
            return result

        intensity = self.get_corruption_intensity(state)

        # Corrupt title
        if "title" in result and result["title"]:
            # Lower corruption rate for titles
            if random.random() < intensity * 0.5:
                result["title"] = self.corrupt_text(
                    result["title"], intensity * 0.5, "glitch"
                )
                result["_title_corrupted"] = True

        # Maybe modify view count (show fake numbers)
        level = self.progress_engine.get_level_from_state(state)
        if level in [ProgressLevel.HIGH, ProgressLevel.CRITICAL]:
            if "views" in result and random.random() < 0.4:
                # Add fake viewers
                result["views"] = result.get("views", 0) + random.randint(3, 13)
                result["_viewers_watching"] = random.randint(2, 7)

        return result

    def generate_fake_post(
        self,
        state: RitualState,
        thread_id: int,
    ) -> dict:
        """
        Generate a fake "ghost" post for anomaly events.

        Args:
            state: User's RitualState
            thread_id: Thread ID for the fake post

        Returns:
            Fake post data
        """
        ghost_contents = [
            "...",
            "Помоги мне.",
            "Ты видишь это?",
            "Они знают, что ты здесь.",
            "НЕ УХОДИ",
            "█████████████",
            "Я вижу тебя.",
            "Почему ты ещё читаешь?",
            "Выход закрыт.",
            "Мы ждали тебя.",
        ]

        ghost_usernames = [
            "???",
            "█████",
            "Неизвестный",
            "[удалено]",
            "Наблюдатель",
            "Он",
            "...",
        ]

        return {
            "id": -1,  # Fake ID
            "thread_id": thread_id,
            "content": random.choice(ghost_contents),
            "username": random.choice(ghost_usernames),
            "created_at": datetime.utcnow().isoformat(),
            "_is_ghost": True,
            "_disappears_in": random.randint(5000, 15000),  # ms
        }

    def create_corruption_overlay(
        self,
        state: RitualState,
    ) -> Optional[dict]:
        """
        Create data for visual corruption overlay.
        Used by frontend for visual effects.

        Args:
            state: User's RitualState

        Returns:
            Overlay configuration or None
        """
        level = self.progress_engine.get_level_from_state(state)

        if level == ProgressLevel.LOW:
            return None

        intensity = self.get_corruption_intensity(state)

        overlay_types = {
            ProgressLevel.MEDIUM: ["static_light", "vignette"],
            ProgressLevel.HIGH: ["static_medium", "scanlines", "vignette"],
            ProgressLevel.CRITICAL: ["static_heavy", "glitch", "vignette", "eyes"],
        }

        available = overlay_types.get(level, [])
        if not available:
            return None

        return {
            "type": random.choice(available),
            "intensity": intensity,
            "duration_ms": random.randint(1000, 5000),
        }
