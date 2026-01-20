#!/usr/bin/env python3
"""
Reusable EventAnalyzer class for exploratory data analysis on event data.

Usage:
    from event_analyzer import EventAnalyzer

    analyzer = EventAnalyzer(events_data)
    summary = analyzer.get_summary()
    temporal = analyzer.analyze_temporal_patterns()
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any


class EventAnalyzer:
    """Analyze event/behavioral data for patterns and insights."""

    def __init__(self, events: list[dict], timestamp_field: str = 'timestamp'):
        """
        Initialize analyzer with event data.

        Args:
            events: List of event dictionaries
            timestamp_field: Name of the timestamp field
        """
        self.events = events
        self.timestamp_field = timestamp_field
        self._parse_timestamps()

    def _parse_timestamps(self):
        """Convert timestamp strings to datetime objects."""
        for event in self.events:
            ts = event.get(self.timestamp_field)
            if isinstance(ts, str):
                # Handle ISO format
                try:
                    event[self.timestamp_field] = datetime.fromisoformat(
                        ts.replace('Z', '+00:00')
                    )
                except ValueError:
                    pass

    def get_summary(self) -> dict:
        """Get high-level summary statistics."""
        timestamps = [e[self.timestamp_field] for e in self.events
                     if self.timestamp_field in e]

        if not timestamps:
            return {'total_events': len(self.events)}

        min_ts = min(timestamps)
        max_ts = max(timestamps)
        date_range_days = (max_ts - min_ts).days or 1

        return {
            'total_events': len(self.events),
            'date_range': f"{min_ts:%Y-%m-%d} to {max_ts:%Y-%m-%d}",
            'date_range_days': date_range_days,
            'events_per_day': round(len(self.events) / date_range_days, 1),
        }

    def count_field(self, field: str, top_n: int = 10) -> list[tuple[str, int]]:
        """Count occurrences of a field value."""
        counter = Counter(
            str(e.get(field, 'unknown'))
            for e in self.events
            if e.get(field)
        )
        return counter.most_common(top_n)

    def analyze_temporal_patterns(self) -> dict:
        """Analyze time-based patterns in events."""
        timestamps = [e[self.timestamp_field] for e in self.events
                     if self.timestamp_field in e and
                     isinstance(e[self.timestamp_field], datetime)]

        if not timestamps:
            return {}

        hourly = Counter([ts.hour for ts in timestamps])
        daily = Counter([ts.strftime('%A') for ts in timestamps])
        monthly = Counter([ts.strftime('%Y-%m') for ts in timestamps])

        return {
            'hourly': dict(sorted(hourly.items())),
            'daily': dict(daily),
            'monthly': dict(sorted(monthly.items())),
            'peak_hour': max(hourly, key=hourly.get) if hourly else None,
            'peak_day': max(daily, key=daily.get) if daily else None,
        }

    def analyze_recency(self, now: datetime = None) -> dict:
        """Analyze recent activity patterns."""
        now = now or datetime.now()
        timestamps = [e[self.timestamp_field] for e in self.events
                     if self.timestamp_field in e and
                     isinstance(e[self.timestamp_field], datetime)]

        if not timestamps:
            return {}

        # Make now offset-aware if timestamps are offset-aware
        if timestamps and timestamps[0].tzinfo is not None and now.tzinfo is None:
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)

        windows = {
            'last_24h': timedelta(hours=24),
            'last_7d': timedelta(days=7),
            'last_30d': timedelta(days=30),
        }

        recency = {}
        for name, delta in windows.items():
            recency[name] = len([ts for ts in timestamps if ts > now - delta])

        return recency

    def get_recent_events(self, n: int = 10, title_field: str = 'title') -> list[dict]:
        """Get most recent events."""
        sorted_events = sorted(
            [e for e in self.events if self.timestamp_field in e],
            key=lambda x: x[self.timestamp_field],
            reverse=True
        )

        return [
            {
                'title': e.get(title_field, 'Unknown'),
                'timestamp': e[self.timestamp_field].isoformat()
                    if isinstance(e[self.timestamp_field], datetime)
                    else str(e[self.timestamp_field])
            }
            for e in sorted_events[:n]
        ]

    def parse_tags(self, tag_string: str) -> list[str]:
        """Parse stringified array format '[tag1, tag2]' to list."""
        if not tag_string or tag_string == '[]':
            return []

        inner = str(tag_string).strip('[]')
        return [t.strip().strip('"\'') for t in inner.split(',') if t.strip()]

    def analyze_tags(self, tag_field: str = 'tags', top_n: int = 30) -> list[tuple[str, int]]:
        """Aggregate and count tags across events."""
        all_tags = Counter()

        for event in self.events:
            tags_value = event.get(tag_field)
            if tags_value:
                tags = self.parse_tags(tags_value)
                all_tags.update(tags)

        return all_tags.most_common(top_n)

    def extract_categories(self, url_field: str = 'url',
                          segment_index: int = 1) -> list[tuple[str, int]]:
        """Extract categories from URL paths."""
        categories = Counter()

        for event in self.events:
            url = event.get(url_field, '')
            if url:
                parts = url.strip('/').split('/')
                if len(parts) > segment_index:
                    categories[parts[segment_index]] += 1

        return categories.most_common(20)

    def get_unique_sample(self, field: str, n: int = 50) -> list[str]:
        """Get unique sample values for a field."""
        seen = set()
        sample = []

        for event in self.events:
            value = event.get(field)
            if value and value not in seen:
                seen.add(value)
                sample.append(value)
                if len(sample) >= n:
                    break

        return sample

    def build_llm_context(self, title_field: str = 'title') -> dict:
        """Build context dictionary suitable for LLM consumption."""
        summary = self.get_summary()
        temporal = self.analyze_temporal_patterns()
        recency = self.analyze_recency()

        return {
            'summary': summary,
            'sample_titles': self.get_unique_sample(title_field, 50),
            'recent_events': self.get_recent_events(10, title_field),
            'temporal_patterns': temporal,
            'recency': recency,
        }


if __name__ == '__main__':
    # Example usage
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python event_analyzer.py <events.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        events = json.load(f)

    analyzer = EventAnalyzer(events)

    print("=== Summary ===")
    print(json.dumps(analyzer.get_summary(), indent=2))

    print("\n=== Temporal Patterns ===")
    print(json.dumps(analyzer.analyze_temporal_patterns(), indent=2))

    print("\n=== Recency ===")
    print(json.dumps(analyzer.analyze_recency(), indent=2))
