"""
Progress Engine for the Ritual Engine.
Manages user progress calculation and threshold levels.
"""

from enum import Enum
from typing import Optional

from app.schemas.ritual import RitualState
from app.utils.time_utils import get_anomaly_multiplier, is_witching_hour


class ProgressLevel(str, Enum):
    """Progress threshold levels affecting anomaly frequency."""
    LOW = "low"           # 0-20%: Rare anomalies
    MEDIUM = "medium"     # 21-50%: Sometimes
    HIGH = "high"         # 51-80%: Often
    CRITICAL = "critical" # 81-100%: Constant


class ProgressEngine:
    """
    Manages progress calculation and threshold levels.

    Progress affects:
    - Anomaly frequency (higher = more frequent)
    - Anomaly intensity (higher = more severe)
    - Content corruption chance
    - Available anomaly types

    Progress sources:
    - Viewing threads/posts
    - Time on site
    - Trigger activations
    - Specific actions
    """

    # Base progress values
    PROGRESS_PER_THREAD_VIEW = 1
    PROGRESS_PER_POST_VIEW = 0.5
    PROGRESS_PER_MINUTE = 0.1
    PROGRESS_PER_UNIQUE_BOARD = 2

    # Progress thresholds
    THRESHOLDS = {
        ProgressLevel.LOW: (0, 20),
        ProgressLevel.MEDIUM: (21, 50),
        ProgressLevel.HIGH: (51, 80),
        ProgressLevel.CRITICAL: (81, 100),
    }

    # Anomaly base chances per level (per request)
    BASE_ANOMALY_CHANCES = {
        ProgressLevel.LOW: 0.02,      # 2% chance
        ProgressLevel.MEDIUM: 0.08,   # 8% chance
        ProgressLevel.HIGH: 0.20,     # 20% chance
        ProgressLevel.CRITICAL: 0.40, # 40% chance
    }

    # Corruption chances per level
    CORRUPTION_CHANCES = {
        ProgressLevel.LOW: 0.0,       # No corruption
        ProgressLevel.MEDIUM: 0.05,   # 5% chance
        ProgressLevel.HIGH: 0.15,     # 15% chance
        ProgressLevel.CRITICAL: 0.35, # 35% chance
    }

    def get_level(self, progress: int) -> ProgressLevel:
        """
        Get progress level from progress value.

        Args:
            progress: Progress value (0-100)

        Returns:
            ProgressLevel enum value
        """
        progress = max(0, min(100, progress))

        for level, (min_val, max_val) in self.THRESHOLDS.items():
            if min_val <= progress <= max_val:
                return level

        return ProgressLevel.CRITICAL

    def get_level_from_state(self, state: RitualState) -> ProgressLevel:
        """Get progress level from RitualState."""
        return self.get_level(state.progress)

    def calculate_thread_view_progress(
        self,
        state: RitualState,
        thread_id: int,
    ) -> int:
        """
        Calculate progress gain from viewing a thread.

        Args:
            state: Current RitualState
            thread_id: Thread being viewed

        Returns:
            Progress points to add
        """
        # First view of thread gives full points
        if thread_id not in state.viewed_threads:
            return int(self.PROGRESS_PER_THREAD_VIEW)

        # Revisits give reduced progress
        return 0

    def calculate_post_view_progress(
        self,
        state: RitualState,
        post_id: int,
    ) -> int:
        """
        Calculate progress gain from viewing a post.

        Args:
            state: Current RitualState
            post_id: Post being viewed

        Returns:
            Progress points to add (rounded)
        """
        if post_id not in state.viewed_posts:
            return 1 if self.PROGRESS_PER_POST_VIEW >= 0.5 else 0

        return 0

    def calculate_time_progress(
        self,
        old_time: int,
        new_time: int,
    ) -> int:
        """
        Calculate progress gain from time spent.

        Args:
            old_time: Previous time_on_site
            new_time: New time_on_site

        Returns:
            Progress points to add
        """
        added_minutes = (new_time - old_time) / 60
        return int(added_minutes * self.PROGRESS_PER_MINUTE)

    def get_anomaly_chance(
        self,
        state: RitualState,
        multiplier: float = 1.0,
    ) -> float:
        """
        Calculate anomaly chance for current request.

        Args:
            state: Current RitualState
            multiplier: Additional multiplier (from triggers)

        Returns:
            Probability of anomaly (0.0 - 1.0)
        """
        level = self.get_level_from_state(state)
        base_chance = self.BASE_ANOMALY_CHANCES[level]

        # Apply time-of-day multiplier
        time_mult = get_anomaly_multiplier()

        # Apply witching hour bonus
        if is_witching_hour():
            time_mult *= 1.5

        # Calculate final chance (capped at 95%)
        final_chance = min(0.95, base_chance * multiplier * time_mult)

        return final_chance

    def get_corruption_chance(
        self,
        state: RitualState,
        multiplier: float = 1.0,
    ) -> float:
        """
        Calculate content corruption chance.

        Args:
            state: Current RitualState
            multiplier: Additional multiplier

        Returns:
            Probability of corruption (0.0 - 1.0)
        """
        level = self.get_level_from_state(state)
        base_chance = self.CORRUPTION_CHANCES[level]

        # Time-of-day affects corruption too
        time_mult = get_anomaly_multiplier()

        return min(0.8, base_chance * multiplier * time_mult)

    def get_corruption_intensity(self, state: RitualState) -> float:
        """
        Get corruption intensity (0.0 - 1.0).

        Higher progress = more intense corruption.

        Args:
            state: Current RitualState

        Returns:
            Intensity value (0.0 - 1.0)
        """
        # Linear scaling with progress
        base_intensity = state.progress / 100

        # Boost at critical level
        if state.progress >= 80:
            base_intensity *= 1.3

        return min(1.0, base_intensity)

    def apply_progress_delta(
        self,
        current_progress: int,
        delta: int,
    ) -> int:
        """
        Apply progress change with bounds checking.

        Args:
            current_progress: Current progress value
            delta: Change to apply (can be negative)

        Returns:
            New progress value (0-100)
        """
        return max(0, min(100, current_progress + delta))

    def get_progress_description(self, progress: int) -> str:
        """
        Get human-readable progress description.

        Args:
            progress: Progress value

        Returns:
            Description string
        """
        level = self.get_level(progress)

        descriptions = {
            ProgressLevel.LOW: "Всё кажется нормальным...",
            ProgressLevel.MEDIUM: "Что-то здесь не так.",
            ProgressLevel.HIGH: "Они знают, что ты здесь.",
            ProgressLevel.CRITICAL: "Ты один из нас теперь.",
        }

        return descriptions[level]

    def estimate_actions_to_next_level(self, state: RitualState) -> Optional[dict]:
        """
        Estimate actions needed to reach next level.

        Args:
            state: Current RitualState

        Returns:
            Dict with estimated actions, or None if at max level
        """
        current_level = self.get_level_from_state(state)
        current_progress = state.progress

        if current_level == ProgressLevel.CRITICAL:
            return None

        # Find next threshold
        next_thresholds = {
            ProgressLevel.LOW: 21,
            ProgressLevel.MEDIUM: 51,
            ProgressLevel.HIGH: 81,
        }

        next_threshold = next_thresholds.get(current_level, 100)
        needed = next_threshold - current_progress

        return {
            "progress_needed": needed,
            "threads_to_view": int(needed / self.PROGRESS_PER_THREAD_VIEW),
            "posts_to_view": int(needed / self.PROGRESS_PER_POST_VIEW),
            "minutes_on_site": int(needed / self.PROGRESS_PER_MINUTE),
            "next_level": self._next_level(current_level).value,
        }

    def _next_level(self, level: ProgressLevel) -> ProgressLevel:
        """Get next progress level."""
        order = [
            ProgressLevel.LOW,
            ProgressLevel.MEDIUM,
            ProgressLevel.HIGH,
            ProgressLevel.CRITICAL,
        ]
        try:
            idx = order.index(level)
            return order[min(idx + 1, len(order) - 1)]
        except ValueError:
            return ProgressLevel.CRITICAL
