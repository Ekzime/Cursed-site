"""
Trigger system for the Ritual Engine.
Checks user behavior and activates triggers based on conditions.
"""

from datetime import datetime
from typing import Callable, List, Optional

from app.schemas.ritual import RitualState
from app.schemas.trigger import (
    TriggerType,
    TriggerEffect,
    TriggerResult,
    TriggerCheckContext,
    TRIGGER_EFFECTS,
)
from app.utils.time_utils import (
    is_night_hour,
    is_witching_hour,
    get_time_of_day,
)


# Type alias for trigger condition function
TriggerCondition = Callable[[TriggerCheckContext], bool]


class TriggerChecker:
    """
    Checks and activates triggers based on user state and behavior.

    Usage:
        checker = TriggerChecker()
        results = checker.check_all(state, current_path="/api/threads/1")
        for result in results:
            if result.activated:
                # Handle trigger activation
    """

    def __init__(self):
        self._conditions = self._build_conditions()

    def _build_conditions(self) -> dict[TriggerType, TriggerCondition]:
        """Build trigger condition functions."""
        return {
            # Visit-based triggers
            TriggerType.FIRST_VISIT: lambda ctx: ctx.progress == 0,

            TriggerType.RETURNEE: lambda ctx: self._check_returnee(ctx),

            TriggerType.FREQUENT_VISITOR: lambda ctx: (
                ctx.known_patterns.get("visit_count", 0) >= 5
            ),

            TriggerType.LATE_NIGHT: lambda ctx: ctx.is_night,

            TriggerType.WITCHING_HOUR: lambda ctx: ctx.is_witching,

            # Reading behavior triggers
            TriggerType.DEEP_READER: lambda ctx: len(ctx.viewed_posts) >= 20,

            TriggerType.SPEED_READER: lambda ctx: self._check_speed_reader(ctx),

            TriggerType.SLOW_READER: lambda ctx: self._check_slow_reader(ctx),

            TriggerType.OBSESSIVE: lambda ctx: self._check_obsessive(ctx),

            TriggerType.EXPLORER: lambda ctx: len(set(
                # Assuming thread IDs can be grouped by board
                # For now, check if viewed many threads
                ctx.viewed_threads
            )) >= 15,

            # Progression triggers
            TriggerType.HALFWAY: lambda ctx: ctx.progress >= 50,

            TriggerType.ALMOST_THERE: lambda ctx: ctx.progress >= 80,

            TriggerType.ENLIGHTENED: lambda ctx: ctx.progress >= 100,

            # Special triggers
            TriggerType.FOUND_HIDDEN: lambda ctx: self._check_found_hidden(ctx),

            TriggerType.PATTERN_SEEKER: lambda ctx: (
                ctx.known_patterns.get("seeking", False) or
                self._check_pattern_seeking(ctx)
            ),

            TriggerType.TOO_LONG: lambda ctx: ctx.time_on_site >= 3600,  # 1 hour

            TriggerType.MARATHON: lambda ctx: ctx.time_on_site >= 10800,  # 3 hours

            # Time-based triggers
            TriggerType.NIGHT_OWL: lambda ctx: (
                ctx.known_patterns.get("night_visits", 0) >= 3
            ),

            TriggerType.DAWN_VISITOR: lambda ctx: (
                get_time_of_day().value == "dawn"
            ),

            # Interaction triggers
            TriggerType.POSTED: lambda ctx: (
                ctx.current_method == "POST" and
                ctx.current_path and "/posts" in ctx.current_path
            ),

            TriggerType.THREAD_CREATOR: lambda ctx: (
                ctx.current_method == "POST" and
                ctx.current_path and "/threads" in ctx.current_path and
                "/posts" not in ctx.current_path
            ),
        }

    def _check_returnee(self, ctx: TriggerCheckContext) -> bool:
        """Check if user is returning after 7+ days."""
        if ctx.first_visit_timestamp == 0:
            return False
        now = datetime.utcnow().timestamp()
        days_since_first = (now - ctx.first_visit_timestamp) / 86400
        return days_since_first >= 7

    def _check_speed_reader(self, ctx: TriggerCheckContext) -> bool:
        """Check if user is reading too fast (many posts in short time)."""
        if ctx.time_on_site < 60:  # Less than a minute
            return False
        posts_per_minute = len(ctx.viewed_posts) / (ctx.time_on_site / 60)
        return posts_per_minute > 5  # More than 5 posts per minute

    def _check_slow_reader(self, ctx: TriggerCheckContext) -> bool:
        """Check if user reads slowly and carefully."""
        if len(ctx.viewed_posts) < 5:
            return False
        avg_time_per_post = ctx.time_on_site / len(ctx.viewed_posts)
        return avg_time_per_post > 60  # More than 1 minute per post

    def _check_obsessive(self, ctx: TriggerCheckContext) -> bool:
        """Check if user is re-reading same content."""
        # Check for duplicate thread views
        thread_views = ctx.viewed_threads
        if len(thread_views) < 5:
            return False
        unique_threads = set(thread_views)
        revisit_ratio = 1 - (len(unique_threads) / len(thread_views))
        return revisit_ratio > 0.5  # More than 50% revisits

    def _check_found_hidden(self, ctx: TriggerCheckContext) -> bool:
        """Check if user found hidden content."""
        if not ctx.current_path:
            return False
        hidden_indicators = ["hidden", "secret", "void", "nightmare"]
        return any(ind in ctx.current_path.lower() for ind in hidden_indicators)

    def _check_pattern_seeking(self, ctx: TriggerCheckContext) -> bool:
        """Check if user exhibits pattern-seeking behavior."""
        # Sequential thread viewing suggests pattern seeking
        threads = ctx.viewed_threads
        if len(threads) < 5:
            return False

        sequential_count = 0
        for i in range(1, len(threads)):
            if abs(threads[i] - threads[i - 1]) == 1:
                sequential_count += 1

        return sequential_count >= 3  # 3+ sequential views

    def build_context(
        self,
        state: RitualState,
        current_path: Optional[str] = None,
        current_method: Optional[str] = None,
    ) -> TriggerCheckContext:
        """Build trigger check context from RitualState."""
        return TriggerCheckContext(
            user_id=state.user_id,
            progress=state.progress,
            viewed_threads=state.viewed_threads,
            viewed_posts=state.viewed_posts,
            time_on_site=state.time_on_site,
            first_visit_timestamp=state.first_visit.timestamp(),
            last_activity_timestamp=state.last_activity.timestamp(),
            triggers_hit=state.triggers_hit,
            known_patterns=state.known_patterns,
            current_path=current_path,
            current_method=current_method,
            is_night=is_night_hour(),
            is_witching=is_witching_hour(),
            time_of_day=get_time_of_day().value,
        )

    def check_trigger(
        self,
        trigger_type: TriggerType,
        ctx: TriggerCheckContext,
    ) -> TriggerResult:
        """
        Check a single trigger.

        Args:
            trigger_type: Type of trigger to check
            ctx: Trigger check context

        Returns:
            TriggerResult with activation status and effect
        """
        condition = self._conditions.get(trigger_type)
        if not condition:
            return TriggerResult(trigger_type=trigger_type, activated=False)

        # Check if already hit (for one-time triggers)
        already_hit = trigger_type.value in ctx.triggers_hit

        try:
            condition_met = condition(ctx)
        except Exception:
            condition_met = False

        if not condition_met:
            return TriggerResult(trigger_type=trigger_type, activated=False)

        # Get effect
        effect = TRIGGER_EFFECTS.get(trigger_type, TriggerEffect())

        return TriggerResult(
            trigger_type=trigger_type,
            activated=True,
            first_activation=not already_hit,
            effect=effect,
            metadata={
                "progress": ctx.progress,
                "time_on_site": ctx.time_on_site,
                "is_night": ctx.is_night,
            },
        )

    def check_all(
        self,
        state: RitualState,
        current_path: Optional[str] = None,
        current_method: Optional[str] = None,
        trigger_types: Optional[List[TriggerType]] = None,
    ) -> List[TriggerResult]:
        """
        Check all triggers (or specified subset).

        Args:
            state: User's RitualState
            current_path: Current request path
            current_method: Current request method
            trigger_types: Optional list of triggers to check (default: all)

        Returns:
            List of TriggerResult for activated triggers only
        """
        ctx = self.build_context(state, current_path, current_method)
        triggers_to_check = trigger_types or list(TriggerType)

        results = []
        for trigger_type in triggers_to_check:
            result = self.check_trigger(trigger_type, ctx)
            if result.activated:
                results.append(result)

        return results

    def check_new_triggers(
        self,
        state: RitualState,
        current_path: Optional[str] = None,
        current_method: Optional[str] = None,
    ) -> List[TriggerResult]:
        """
        Check only triggers that haven't been hit yet.

        Args:
            state: User's RitualState
            current_path: Current request path
            current_method: Current request method

        Returns:
            List of newly activated TriggerResult
        """
        ctx = self.build_context(state, current_path, current_method)

        results = []
        for trigger_type in TriggerType:
            # Skip already hit triggers
            if trigger_type.value in ctx.triggers_hit:
                continue

            result = self.check_trigger(trigger_type, ctx)
            if result.activated:
                results.append(result)

        return results

    def get_applicable_effects(
        self,
        results: List[TriggerResult],
    ) -> dict:
        """
        Aggregate effects from multiple trigger results.

        Args:
            results: List of activated trigger results

        Returns:
            Aggregated effects dict with:
            - total_progress_delta: Sum of progress changes
            - max_anomaly_multiplier: Maximum anomaly multiplier
            - unlocks: List of unlocked boards/threads
            - force_anomalies: List of forced anomaly types
            - messages: List of messages to show
        """
        total_progress = 0
        max_multiplier = 1.0
        unlocks_boards = []
        unlocks_threads = []
        force_anomalies = []
        messages = []
        patterns_to_set = {}

        for result in results:
            if not result.effect:
                continue

            effect = result.effect

            # Only apply progress/messages on first activation
            if result.first_activation:
                total_progress += effect.progress_delta
                if effect.message:
                    messages.append(effect.message)
                if effect.unlock_board:
                    unlocks_boards.append(effect.unlock_board)
                if effect.unlock_thread:
                    unlocks_threads.append(effect.unlock_thread)
                if effect.set_pattern:
                    patterns_to_set.update(effect.set_pattern)

            # Always apply multiplier
            if effect.anomaly_chance_multiplier > max_multiplier:
                max_multiplier = effect.anomaly_chance_multiplier

            if effect.force_anomaly:
                force_anomalies.append(effect.force_anomaly)

        return {
            "total_progress_delta": total_progress,
            "max_anomaly_multiplier": max_multiplier,
            "unlocks_boards": unlocks_boards,
            "unlocks_threads": unlocks_threads,
            "force_anomalies": force_anomalies,
            "messages": messages,
            "patterns_to_set": patterns_to_set,
        }
