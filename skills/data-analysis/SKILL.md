---
name: data-analysis
description: Perform exploratory data analysis on event, behavioral, or time-series data. Use when analyzing user events, clickstream data, engagement metrics, or any dataset requiring temporal patterns, frequency distributions, and summary statistics. Triggers on requests for data analysis, EDA, user behavior analysis, or event exploration.
---

# Data Analysis

Exploratory data analysis skill for event-based and behavioral datasets. Use this for analyzing user events, clickstream data, engagement metrics, and time-series patterns.

## Quick Start

```python
import pandas as pd
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# Load and prepare data
df = pd.read_json('events.json')
df['timestamp'] = pd.to_datetime(df['timestamp'])
```

## Core Analysis Patterns

### 1. Frequency Distribution
Count occurrences of categorical fields:
```python
# Top items by count
counter = Counter(df['category'])
top_10 = counter.most_common(10)

# With percentage
total = sum(counter.values())
for item, count in top_10:
    pct = (count / total) * 100
    print(f"{item}: {count} ({pct:.1f}%)")
```

### 2. Temporal Pattern Analysis
Extract time-based insights:
```python
# By hour (activity peaks)
hourly = Counter([ts.hour for ts in df['timestamp']])

# By day of week
daily = Counter([ts.day_name() for ts in df['timestamp']])

# By month
monthly = df.groupby(df['timestamp'].dt.to_period('M')).size()

# Recent activity (last 7 days)
now = datetime.now()
recent = df[df['timestamp'] > now - timedelta(days=7)]
```

### 3. Engagement Metrics
Calculate key engagement indicators:
```python
date_range = (df['timestamp'].max() - df['timestamp'].min()).days
events_per_day = len(df) / max(date_range, 1)
unique_items = df['item_id'].nunique()
repeat_rate = len(df) / unique_items  # Items viewed multiple times
```

### 4. Parse Stringified Arrays
Handle JSON arrays stored as strings (common in event data):
```python
import re

def parse_tags(tag_string):
    """Parse '[tag1, tag2]' format to list."""
    if not tag_string or tag_string == '[]':
        return []
    # Remove brackets and split
    inner = tag_string.strip('[]')
    return [t.strip().strip('"\'') for t in inner.split(',') if t.strip()]

all_tags = Counter()
for tags_str in df['tags']:
    all_tags.update(parse_tags(tags_str))
```

### 5. Category Extraction from URLs
Extract content taxonomy from URL paths:
```python
def extract_category(url):
    """Extract category from /section/category/slug pattern."""
    parts = url.strip('/').split('/')
    if len(parts) >= 2:
        return parts[1]  # Second segment is usually category
    return 'uncategorized'

categories = Counter(df['url'].apply(extract_category))
```

### 6. Cross-Platform/Source Analysis
Group events by source or platform:
```python
# Group by domain/source
sources = defaultdict(list)
for _, row in df.iterrows():
    domain = row['domain'] or 'unknown'
    sources[domain].append(row)

# Summary per source
for source, events in sources.items():
    print(f"{source}: {len(events)} events")
```

## Timezone Handling

Infer timezone from activity peaks:
```python
def estimate_timezone(hourly_counts):
    """Estimate timezone from peak activity hours (assuming daytime usage)."""
    peak_hour = max(hourly_counts, key=hourly_counts.get)

    # Assume peak activity is around 12-18 local time
    if 12 <= peak_hour <= 18:
        return 'UTC', 0
    elif 17 <= peak_hour <= 23:
        return 'US/Eastern', -5
    elif 19 <= peak_hour or peak_hour <= 4:
        return 'US/Pacific', -8
    else:
        return 'US/Mountain', -7
```

## Output Patterns

### Summary Statistics
```python
summary = {
    'total_events': len(df),
    'unique_items': df['item_id'].nunique(),
    'date_range': f"{df['timestamp'].min():%Y-%m-%d} to {df['timestamp'].max():%Y-%m-%d}",
    'events_per_day': round(events_per_day, 1),
    'top_categories': dict(categories.most_common(5)),
    'peak_hour': max(hourly, key=hourly.get),
    'peak_day': max(daily, key=daily.get),
}
```

### Sampled Context for LLM Analysis
When preparing data for LLM narrative generation:
```python
# Sample unique titles (avoid duplicates)
unique_titles = df['title'].drop_duplicates().head(50).tolist()

# Recent activity
recent_events = df.nlargest(10, 'timestamp')[['title', 'timestamp']].to_dict('records')

# Build context
context = {
    'sample_titles': unique_titles,
    'recent_events': recent_events,
    'summary': summary,
}
```

## Bundled Resources

For detailed patterns and advanced techniques, see:
- [references/temporal-patterns.md](references/temporal-patterns.md) - Deep dive on time-series analysis
- [references/llm-context.md](references/llm-context.md) - Preparing data for LLM narrative generation
- [scripts/event_analyzer.py](scripts/event_analyzer.py) - Reusable EventAnalyzer class

## Best Practices

1. **Always explore first**: Check data types, null values, and distributions before analysis
2. **Use Counter for frequencies**: More efficient than pandas value_counts for large datasets
3. **Sample before LLM calls**: 50-100 unique items is usually sufficient context
4. **Handle missing data gracefully**: Use `or 'unknown'` patterns
5. **Calculate relative metrics**: Percentages and rates are more meaningful than raw counts
