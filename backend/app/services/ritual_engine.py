"""
Ritual Engine - Main orchestrator for the curse system.
Coordinates all ritual components: state, triggers, anomalies, and content mutations.
"""

import logging
from typing import Optional, List, Tuple

import redis.asyncio as redis

from app.schemas.ritual import RitualState
from app.schemas.anomaly import AnomalyEvent, AnomalyType
from app.schemas.trigger import TriggerResult
from app.services.ritual_state import RitualStateManager
from app.services.triggers import TriggerChecker
from app.services.progress_engine import ProgressEngine, ProgressLevel
from app.services.anomaly_generator import AnomalyGenerator
from app.services.anomaly_queue import AnomalyQueue, ConnectionManager
from app.services.content_mutator import ContentMutator


logger = logging.getLogger(__name__)


class RitualEngine:
    """
    Main orchestrator for the Ritual/Curse system.

    Coordinates:
    - RitualStateManager: User state persistence
    - TriggerChecker: Behavior-based trigger activation
    - ProgressEngine: Progress calculation and thresholds
    - AnomalyGenerator: Random anomaly creation
    - AnomalyQueue: Real-time event delivery
    - ContentMutator: Text corruption

    Usage:
        engine = RitualEngine(redis_client)

        # On each request
        state, is_new = await engine.on_request(user_id, path, method)

        # On content view
        await engine.on_thread_view(user_id, thread_id)

        # Mutate content before response
        mutated_post = engine.mutate_post(post_dict, state)
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

        # Initialize all services
        self.state_manager = RitualStateManager(redis_client)
        self.trigger_checker = TriggerChecker()
        self.progress_engine = ProgressEngine()
        self.anomaly_generator = AnomalyGenerator()
        self.anomaly_queue = AnomalyQueue(redis_client)
        self.connection_manager = ConnectionManager(redis_client)
        self.content_mutator = ContentMutator()

    async def on_request(
        self,
        user_id: str,
        path: Optional[str] = None,
        method: Optional[str] = None,
    ) -> Tuple[RitualState, bool]:
        """
        Process incoming request for a user.
        Called by middleware on each API request.

        Args:
            user_id: User identifier
            path: Request path
            method: HTTP method

        Returns:
            Tuple of (RitualState, is_new_visitor)
        """
        # Get or create state
        state, is_new = await self.state_manager.get_or_create(user_id)

        if is_new:
            logger.info(f"New visitor: {user_id}")

        # Check triggers
        trigger_results = self.trigger_checker.check_new_triggers(
            state, path, method
        )

        # Process trigger effects
        if trigger_results:
            await self._process_triggers(user_id, state, trigger_results)

        # Maybe generate random anomaly
        await self._maybe_generate_anomaly(user_id, state)

        # Save updated state
        await self.state_manager.save(state)

        return state, is_new

    async def on_thread_view(
        self,
        user_id: str,
        thread_id: int,
    ) -> Optional[RitualState]:
        """
        Process thread view event.

        Args:
            user_id: User identifier
            thread_id: Thread being viewed

        Returns:
            Updated RitualState or None
        """
        state = await self.state_manager.get(user_id)
        if not state:
            return None

        # Calculate progress
        progress_delta = self.progress_engine.calculate_thread_view_progress(
            state, thread_id
        )

        # Update state
        if thread_id not in state.viewed_threads:
            state.viewed_threads.append(thread_id)
            if len(state.viewed_threads) > 100:
                state.viewed_threads = state.viewed_threads[-100:]

        if progress_delta > 0:
            state.progress = self.progress_engine.apply_progress_delta(
                state.progress, progress_delta
            )

        await self.state_manager.save(state)

        return state

    async def on_post_view(
        self,
        user_id: str,
        post_id: int,
    ) -> Optional[RitualState]:
        """
        Process post view event.

        Args:
            user_id: User identifier
            post_id: Post being viewed

        Returns:
            Updated RitualState or None
        """
        state = await self.state_manager.get(user_id)
        if not state:
            return None

        # Calculate progress
        progress_delta = self.progress_engine.calculate_post_view_progress(
            state, post_id
        )

        # Update state
        if post_id not in state.viewed_posts:
            state.viewed_posts.append(post_id)
            if len(state.viewed_posts) > 500:
                state.viewed_posts = state.viewed_posts[-500:]

        if progress_delta > 0:
            state.progress = self.progress_engine.apply_progress_delta(
                state.progress, progress_delta
            )

        await self.state_manager.save(state)

        return state

    async def queue_anomaly(
        self,
        user_id: str,
        event: AnomalyEvent,
    ) -> int:
        """
        Queue an anomaly for delivery via WebSocket.

        Args:
            user_id: Target user ID
            event: Anomaly event to queue

        Returns:
            Queue length after push
        """
        return await self.anomaly_queue.push(user_id, event)

    async def queue_anomaly_for_type(
        self,
        user_id: str,
        anomaly_type: AnomalyType,
        target_id: Optional[int] = None,
        custom_data: Optional[dict] = None,
    ) -> Optional[AnomalyEvent]:
        """
        Generate and queue a specific anomaly type.

        Args:
            user_id: Target user ID
            anomaly_type: Type of anomaly
            target_id: Optional target post/thread ID
            custom_data: Optional custom data

        Returns:
            Generated event or None if user not found
        """
        state = await self.state_manager.get(user_id)
        if not state:
            return None

        event = self.anomaly_generator.generate_specific(
            anomaly_type, state, target_id, custom_data
        )
        await self.anomaly_queue.push(user_id, event)

        return event

    def mutate_post(
        self,
        post_data: dict,
        state: RitualState,
    ) -> dict:
        """
        Apply curse mutations to a post.

        Args:
            post_data: Post data dict
            state: User's RitualState

        Returns:
            Mutated post data
        """
        return self.content_mutator.mutate_post(post_data, state)

    def mutate_thread(
        self,
        thread_data: dict,
        state: RitualState,
    ) -> dict:
        """
        Apply curse mutations to a thread.

        Args:
            thread_data: Thread data dict
            state: User's RitualState

        Returns:
            Mutated thread data
        """
        return self.content_mutator.mutate_thread(thread_data, state)

    def mutate_posts_list(
        self,
        posts: List[dict],
        state: RitualState,
    ) -> List[dict]:
        """
        Apply mutations to a list of posts.

        Args:
            posts: List of post data dicts
            state: User's RitualState

        Returns:
            List of mutated post data
        """
        return [self.mutate_post(p, state) for p in posts]

    async def get_user_state(self, user_id: str) -> Optional[RitualState]:
        """Get user's current RitualState."""
        return await self.state_manager.get(user_id)

    async def reset_user_state(self, user_id: str) -> RitualState:
        """Reset user's state to initial values."""
        await self.state_manager.delete(user_id)
        state, _ = await self.state_manager.get_or_create(user_id)
        return state

    async def set_user_progress(
        self,
        user_id: str,
        progress: int,
    ) -> Optional[RitualState]:
        """Set user's progress to a specific value."""
        return await self.state_manager.set_progress(user_id, progress)

    async def get_connected_users(self) -> List[str]:
        """Get list of users with active WebSocket connections."""
        return await self.connection_manager.get_connected_users()

    async def get_connection_count(self) -> int:
        """Get number of active WebSocket connections."""
        return await self.connection_manager.get_connection_count()

    async def _process_triggers(
        self,
        user_id: str,
        state: RitualState,
        results: List[TriggerResult],
    ) -> None:
        """Process activated triggers and their effects."""
        effects = self.trigger_checker.get_applicable_effects(results)

        # Apply progress changes
        if effects["total_progress_delta"] != 0:
            state.progress = self.progress_engine.apply_progress_delta(
                state.progress, effects["total_progress_delta"]
            )

        # Record triggers
        for result in results:
            if result.first_activation:
                state.triggers_hit.add(result.trigger_type.value)
                logger.info(
                    f"Trigger activated for {user_id}: {result.trigger_type.value}"
                )

        # Update patterns
        for key, value in effects["patterns_to_set"].items():
            state.known_patterns[key] = value

        # Queue forced anomalies
        for anomaly_type_str in effects["force_anomalies"]:
            try:
                anomaly_type = AnomalyType(anomaly_type_str)
                event = self.anomaly_generator.generate_specific(
                    anomaly_type, state, triggered_by="trigger"
                )
                await self.anomaly_queue.push(user_id, event)
            except ValueError:
                logger.warning(f"Unknown anomaly type: {anomaly_type_str}")

    async def _maybe_generate_anomaly(
        self,
        user_id: str,
        state: RitualState,
    ) -> None:
        """Maybe generate a random anomaly based on progress."""
        # Only for connected users
        is_connected = await self.connection_manager.is_connected(user_id)
        if not is_connected:
            return

        # Check if should generate
        if self.anomaly_generator.should_generate(state):
            event = self.anomaly_generator.generate(state)
            await self.anomaly_queue.push(user_id, event)
            logger.debug(f"Generated anomaly for {user_id}: {event.type.value}")
