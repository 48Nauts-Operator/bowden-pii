"""Placeholder creation and local placeholder maps."""

from __future__ import annotations

from collections import defaultdict

from bowden_pii.types import Detection, PlaceholderEntry


class PlaceholderBuilder:
    def __init__(self) -> None:
        self._counts: dict[str, int] = defaultdict(int)
        self.placeholder_map: dict[str, PlaceholderEntry] = {}
        self._by_key: dict[tuple[str, str], str] = {}

    def placeholder_for(self, detection: Detection) -> str:
        key = (detection.label, detection.normalized or detection.value)
        existing = self._by_key.get(key)
        if existing is not None:
            return existing

        self._counts[detection.label] += 1
        placeholder = f"[{detection.label}_{self._counts[detection.label]}]"
        self._by_key[key] = placeholder
        self.placeholder_map[placeholder] = PlaceholderEntry(
            label=detection.label,
            value=detection.value,
            source=detection.source,
            rule_id=detection.rule_id,
            normalized=detection.normalized,
        )
        return placeholder
