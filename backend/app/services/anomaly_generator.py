"""
Anomaly Generator for the Ritual Engine.
Generates anomalies based on user progress and state.
"""

import random
from typing import Optional, List, Tuple

from app.schemas.ritual import RitualState
from app.schemas.anomaly import (
    AnomalyType,
    AnomalySeverity,
    AnomalyEvent,
    create_anomaly,
)
from app.services.progress_engine import ProgressEngine, ProgressLevel
from app.utils.time_utils import get_anomaly_multiplier, is_witching_hour


class AnomalyGenerator:
    """
    Generates anomalies based on user state and progress level.

    Anomaly pools are divided by progress level.
    Higher progress = more frequent and intense anomalies.

    Usage:
        generator = AnomalyGenerator()

        # Check if should generate
        if generator.should_generate(state):
            event = generator.generate(state)
            await queue.push(user_id, event)

        # Force specific anomaly
        event = generator.generate_specific(
            AnomalyType.WHISPER,
            state,
            custom_data={"message": "I see you"}
        )
    """

    # Anomaly pools by progress level
    # Format: (AnomalyType, weight)
    ANOMALY_POOLS: dict[ProgressLevel, List[Tuple[AnomalyType, float]]] = {
        ProgressLevel.LOW: [
            (AnomalyType.GLITCH, 0.3),
            (AnomalyType.FLICKER, 0.3),
            (AnomalyType.STATIC, 0.2),
            (AnomalyType.VIEWER_COUNT, 0.2),
        ],
        ProgressLevel.MEDIUM: [
            (AnomalyType.GLITCH, 0.15),
            (AnomalyType.FLICKER, 0.15),
            (AnomalyType.WHISPER, 0.2),
            (AnomalyType.PRESENCE, 0.2),
            (AnomalyType.NEW_POST, 0.15),
            (AnomalyType.POST_EDIT, 0.15),
        ],
        ProgressLevel.HIGH: [
            (AnomalyType.POST_CORRUPT, 0.15),
            (AnomalyType.WHISPER, 0.15),
            (AnomalyType.PRESENCE, 0.15),
            (AnomalyType.SHADOW, 0.1),
            (AnomalyType.NOTIFICATION, 0.15),
            (AnomalyType.RECOGNITION, 0.1),
            (AnomalyType.TYPING, 0.1),
            (AnomalyType.CURSOR, 0.1),
        ],
        ProgressLevel.CRITICAL: [
            (AnomalyType.POST_CORRUPT, 0.12),
            (AnomalyType.PRESENCE, 0.12),
            (AnomalyType.SHADOW, 0.1),
            (AnomalyType.EYES, 0.1),
            (AnomalyType.RECOGNITION, 0.12),
            (AnomalyType.MEMORY, 0.1),
            (AnomalyType.TYPING, 0.1),
            (AnomalyType.HEARTBEAT, 0.12),
            (AnomalyType.SCROLL, 0.06),
            (AnomalyType.POST_DELETE, 0.06),
        ],
    }

    # Severity distribution by progress level
    SEVERITY_WEIGHTS: dict[ProgressLevel, dict[AnomalySeverity, float]] = {
        ProgressLevel.LOW: {
            AnomalySeverity.SUBTLE: 0.7,
            AnomalySeverity.MILD: 0.3,
        },
        ProgressLevel.MEDIUM: {
            AnomalySeverity.SUBTLE: 0.3,
            AnomalySeverity.MILD: 0.4,
            AnomalySeverity.MODERATE: 0.3,
        },
        ProgressLevel.HIGH: {
            AnomalySeverity.MILD: 0.2,
            AnomalySeverity.MODERATE: 0.4,
            AnomalySeverity.INTENSE: 0.4,
        },
        ProgressLevel.CRITICAL: {
            AnomalySeverity.MODERATE: 0.2,
            AnomalySeverity.INTENSE: 0.5,
            AnomalySeverity.EXTREME: 0.3,
        },
    }

    # Special messages for recognition/memory anomalies
    WHISPER_MESSAGES = [
        "...ты слышишь нас?...",
        "...не уходи...",
        "...мы знаем...",
        "...скоро...",
        "...оглянись...",
        "...ты не один...",
        "...помнишь?...",
    ]

    RECOGNITION_MESSAGES = [
        "Добро пожаловать обратно.",
        "Мы ждали тебя.",
        "Ты вернулся.",
        "Мы помним твоё лицо.",
        "Время здесь течёт иначе.",
    ]

    PRESENCE_MESSAGES = [
        "Кто-то смотрит на тебя.",
        "Ты не один здесь.",
        "Они рядом.",
        "Что-то следит за тобой.",
        "Тень движется.",
    ]

    def __init__(self):
        self.progress_engine = ProgressEngine()

    def should_generate(
        self,
        state: RitualState,
        multiplier: float = 1.0,
    ) -> bool:
        """
        Determine if an anomaly should be generated.

        Args:
            state: User's RitualState
            multiplier: Additional multiplier (from triggers)

        Returns:
            True if anomaly should be generated
        """
        chance = self.progress_engine.get_anomaly_chance(state, multiplier)
        return random.random() < chance

    def generate(
        self,
        state: RitualState,
        target_id: Optional[int] = None,
        triggered_by: Optional[str] = None,
    ) -> AnomalyEvent:
        """
        Generate a random anomaly appropriate for user's progress level.

        Args:
            state: User's RitualState
            target_id: Optional target post/thread ID
            triggered_by: Optional trigger name

        Returns:
            Generated AnomalyEvent
        """
        level = self.progress_engine.get_level_from_state(state)

        # Select anomaly type from pool
        anomaly_type = self._select_anomaly_type(level)

        # Select severity
        severity = self._select_severity(level)

        # Generate custom data
        custom_data = self._generate_custom_data(
            anomaly_type, state, level
        )

        return create_anomaly(
            anomaly_type=anomaly_type,
            severity=severity,
            target_id=target_id,
            custom_data=custom_data,
            triggered_by=triggered_by,
        )

    def generate_specific(
        self,
        anomaly_type: AnomalyType,
        state: RitualState,
        target_id: Optional[int] = None,
        custom_data: Optional[dict] = None,
        triggered_by: Optional[str] = None,
    ) -> AnomalyEvent:
        """
        Generate a specific anomaly type.

        Args:
            anomaly_type: Type of anomaly to generate
            state: User's RitualState
            target_id: Optional target post/thread ID
            custom_data: Optional custom data to include
            triggered_by: Optional trigger name

        Returns:
            Generated AnomalyEvent
        """
        level = self.progress_engine.get_level_from_state(state)
        severity = self._select_severity(level)

        # Merge with generated custom data
        generated_data = self._generate_custom_data(
            anomaly_type, state, level
        )
        if custom_data:
            generated_data.update(custom_data)

        return create_anomaly(
            anomaly_type=anomaly_type,
            severity=severity,
            target_id=target_id,
            custom_data=generated_data,
            triggered_by=triggered_by,
        )

    def generate_batch(
        self,
        state: RitualState,
        count: int,
    ) -> List[AnomalyEvent]:
        """
        Generate multiple anomalies for burst effects.

        Args:
            state: User's RitualState
            count: Number of anomalies to generate

        Returns:
            List of AnomalyEvents with varying delays
        """
        events = []
        base_delay = 0

        for i in range(count):
            event = self.generate(state)
            # Stagger delays
            event.delay_ms = base_delay + random.randint(500, 2000)
            base_delay = event.delay_ms
            events.append(event)

        return events

    def _select_anomaly_type(self, level: ProgressLevel) -> AnomalyType:
        """Select anomaly type from pool based on weights."""
        pool = self.ANOMALY_POOLS.get(level, self.ANOMALY_POOLS[ProgressLevel.LOW])

        types = [item[0] for item in pool]
        weights = [item[1] for item in pool]

        return random.choices(types, weights=weights, k=1)[0]

    def _select_severity(self, level: ProgressLevel) -> AnomalySeverity:
        """Select severity based on level weights."""
        weights_dict = self.SEVERITY_WEIGHTS.get(
            level, self.SEVERITY_WEIGHTS[ProgressLevel.LOW]
        )

        severities = list(weights_dict.keys())
        weights = list(weights_dict.values())

        return random.choices(severities, weights=weights, k=1)[0]

    def _generate_custom_data(
        self,
        anomaly_type: AnomalyType,
        state: RitualState,
        level: ProgressLevel,
    ) -> dict:
        """Generate custom data based on anomaly type and state."""
        data = {}

        if anomaly_type == AnomalyType.WHISPER:
            data["message"] = random.choice(self.WHISPER_MESSAGES)

        elif anomaly_type == AnomalyType.PRESENCE:
            data["message"] = random.choice(self.PRESENCE_MESSAGES)

        elif anomaly_type == AnomalyType.RECOGNITION:
            data["message"] = random.choice(self.RECOGNITION_MESSAGES)

        elif anomaly_type == AnomalyType.MEMORY:
            # Reference something user has seen
            if state.viewed_threads:
                thread_id = random.choice(state.viewed_threads)
                data["referenced_thread"] = thread_id
                data["message"] = f"Помнишь тот тред? Он помнит тебя."

        elif anomaly_type == AnomalyType.VIEWER_COUNT:
            # Fake viewer count
            base = random.randint(3, 12)
            # Higher at night
            if is_witching_hour():
                base += random.randint(10, 30)
            data["count"] = base
            data["message"] = f"Сейчас читают: {base}"

        elif anomaly_type == AnomalyType.POST_CORRUPT:
            # Corruption intensity based on level
            intensity_map = {
                ProgressLevel.LOW: 0.1,
                ProgressLevel.MEDIUM: 0.3,
                ProgressLevel.HIGH: 0.5,
                ProgressLevel.CRITICAL: 0.8,
            }
            data["corruption_level"] = intensity_map.get(level, 0.3)

        elif anomaly_type == AnomalyType.GLITCH:
            effects = ["rgb_split", "scanlines", "noise", "displacement"]
            data["effect"] = random.choice(effects)

        elif anomaly_type == AnomalyType.TYPING:
            typing_texts = [
                "ОНИ ЗДЕСЬ",
                "ПОМОГИ",
                "НЕ УХОДИ",
                "Я ВИЖУ ТЕБЯ",
                "СКОРО",
            ]
            data["text"] = random.choice(typing_texts)

        elif anomaly_type == AnomalyType.CURSOR:
            behaviors = ["drift", "shake", "follow", "avoid"]
            data["behavior"] = random.choice(behaviors)

        elif anomaly_type == AnomalyType.HEARTBEAT:
            # BPM increases with progress
            base_bpm = 60 + (state.progress * 0.6)  # 60-120 BPM
            data["bpm"] = int(base_bpm)

        return data

    def get_night_burst_count(self, level: ProgressLevel) -> int:
        """Get number of anomalies for night burst based on level."""
        counts = {
            ProgressLevel.LOW: 1,
            ProgressLevel.MEDIUM: 2,
            ProgressLevel.HIGH: 4,
            ProgressLevel.CRITICAL: 7,
        }
        return counts.get(level, 1)

    def get_witching_hour_burst(
        self,
        state: RitualState,
    ) -> List[AnomalyEvent]:
        """Generate special witching hour burst (2-5 AM)."""
        level = self.progress_engine.get_level_from_state(state)

        # Special anomaly types for witching hour
        witching_types = [
            AnomalyType.SHADOW,
            AnomalyType.EYES,
            AnomalyType.WHISPER,
            AnomalyType.PRESENCE,
            AnomalyType.HEARTBEAT,
        ]

        events = []
        count = self.get_night_burst_count(level) + 2  # Extra for witching

        for i in range(count):
            anomaly_type = random.choice(witching_types)
            event = self.generate_specific(
                anomaly_type,
                state,
                triggered_by="witching_hour",
            )
            event.severity = AnomalySeverity.INTENSE
            event.delay_ms = i * random.randint(2000, 5000)
            events.append(event)

        return events
