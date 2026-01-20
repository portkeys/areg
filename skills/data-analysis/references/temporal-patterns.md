# Temporal Pattern Analysis

Deep dive on time-series analysis for event data.

## Time Window Analysis

### Rolling Windows
```python
import pandas as pd

# 7-day rolling average
df['rolling_7d'] = df.set_index('timestamp')['events'].rolling('7D').mean()

# 30-day rolling sum
df['rolling_30d_sum'] = df.set_index('timestamp')['events'].rolling('30D').sum()
```

### Period Comparison
```python
from datetime import datetime, timedelta

now = datetime.now()
last_week = df[df['timestamp'] > now - timedelta(days=7)]
prev_week = df[(df['timestamp'] > now - timedelta(days=14)) &
               (df['timestamp'] <= now - timedelta(days=7))]

change_pct = ((len(last_week) - len(prev_week)) / len(prev_week)) * 100
```

## Seasonality Detection

### Hourly Patterns
```python
from collections import Counter

hourly = Counter([ts.hour for ts in df['timestamp']])

# Find peak hours (top 3)
peak_hours = sorted(hourly.items(), key=lambda x: -x[1])[:3]

# Classify activity pattern
morning_activity = sum(hourly.get(h, 0) for h in range(6, 12))
afternoon_activity = sum(hourly.get(h, 0) for h in range(12, 18))
evening_activity = sum(hourly.get(h, 0) for h in range(18, 24))

if evening_activity > morning_activity and evening_activity > afternoon_activity:
    pattern = "evening-focused"
elif morning_activity > afternoon_activity:
    pattern = "morning-focused"
else:
    pattern = "daytime-focused"
```

### Day of Week Patterns
```python
# Named days
daily = Counter([ts.day_name() for ts in df['timestamp']])

# Weekday vs Weekend
weekday_count = sum(daily.get(d, 0) for d in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
weekend_count = sum(daily.get(d, 0) for d in ['Saturday', 'Sunday'])

weekday_avg = weekday_count / 5
weekend_avg = weekend_count / 2

if weekend_avg > weekday_avg * 1.2:
    pattern = "weekend-heavy"
elif weekday_avg > weekend_avg * 1.2:
    pattern = "weekday-heavy"
else:
    pattern = "consistent"
```

### Monthly Trends
```python
# Group by year-month
monthly = df.groupby(df['timestamp'].dt.to_period('M')).size()

# Detect trend direction
if len(monthly) >= 3:
    recent_3 = monthly.tail(3).mean()
    earlier_3 = monthly.head(3).mean()

    if recent_3 > earlier_3 * 1.1:
        trend = "increasing"
    elif recent_3 < earlier_3 * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"
```

## Recency Analysis

### Activity Decay
```python
from datetime import datetime, timedelta

now = datetime.now()

windows = {
    'last_24h': timedelta(hours=24),
    'last_7d': timedelta(days=7),
    'last_30d': timedelta(days=30),
    'last_90d': timedelta(days=90),
}

recency = {}
for name, delta in windows.items():
    recency[name] = len(df[df['timestamp'] > now - delta])

# Calculate decay rate
if recency['last_90d'] > 0:
    decay_30_to_90 = recency['last_30d'] / (recency['last_90d'] / 3)
    # > 1 means recent activity is higher than average
```

### Streak Detection
```python
# Find consecutive active days
dates = sorted(set(df['timestamp'].dt.date))
current_streak = 0
max_streak = 0

for i, date in enumerate(dates):
    if i == 0:
        current_streak = 1
    elif (date - dates[i-1]).days == 1:
        current_streak += 1
    else:
        max_streak = max(max_streak, current_streak)
        current_streak = 1

max_streak = max(max_streak, current_streak)
```

## Interest Evolution

### Emerging vs Declining Topics
```python
# Split data into halves
midpoint = df['timestamp'].median()
first_half = df[df['timestamp'] <= midpoint]
second_half = df[df['timestamp'] > midpoint]

# Count topics in each half
first_topics = Counter(first_half['topic'])
second_topics = Counter(second_half['topic'])

# Find emerging topics (much higher in second half)
emerging = []
for topic, count in second_topics.most_common():
    first_count = first_topics.get(topic, 0)
    if count > first_count * 2 and count >= 5:
        emerging.append((topic, count, first_count))

# Find declining topics
declining = []
for topic, count in first_topics.most_common():
    second_count = second_topics.get(topic, 0)
    if count > second_count * 2 and count >= 5:
        declining.append((topic, count, second_count))
```

## Timezone Inference

```python
def infer_timezone_from_activity(hourly_counts):
    """
    Infer user's timezone based on activity patterns.
    Assumes most activity occurs between 8am-10pm local time.
    """
    # Find the 4-hour window with most activity
    max_activity = 0
    peak_start = 0

    for start_hour in range(24):
        window_activity = sum(
            hourly_counts.get((start_hour + h) % 24, 0)
            for h in range(4)
        )
        if window_activity > max_activity:
            max_activity = window_activity
            peak_start = start_hour

    # Map peak to likely timezone
    # If peak is 12-16 UTC, likely US Mountain (UTC-7)
    # If peak is 17-21 UTC, likely US Eastern (UTC-5)
    # If peak is 20-24 or 0-4 UTC, likely US Pacific (UTC-8)

    tz_mapping = {
        (8, 12): ('UTC', 0),
        (12, 16): ('US/Mountain', -7),
        (17, 21): ('US/Eastern', -5),
        (20, 24): ('US/Pacific', -8),
        (0, 4): ('US/Pacific', -8),
    }

    for (start, end), (tz_name, offset) in tz_mapping.items():
        if start <= peak_start < end:
            return tz_name, offset

    return 'UTC', 0
```
