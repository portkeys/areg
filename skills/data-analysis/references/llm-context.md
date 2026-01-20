# LLM Context Preparation

Guidelines for preparing event data as context for LLM-powered narrative generation.

## Context Building Strategy

### Sample Size Guidelines

| Data Type | Recommended Sample | Notes |
|-----------|-------------------|-------|
| Unique titles/items | 50-100 | Deduplicated, representative |
| Recent events | 10-20 | Last 7 days, with timestamps |
| Top categories | 10-15 | By frequency |
| Top tags/topics | 20-30 | Aggregated counts |
| Authors/sources | 10-15 | If available |

### Sampling Patterns

```python
import json
from collections import Counter

def build_llm_context(df, max_titles=50, max_recent=10):
    """Build context dict for LLM consumption."""

    # Unique titles (avoid repetition in context)
    unique_titles = df['title'].drop_duplicates().head(max_titles).tolist()

    # Recent activity with timestamps
    recent = df.nlargest(max_recent, 'timestamp')[['title', 'timestamp']]
    recent_events = [
        {'title': row['title'], 'date': row['timestamp'].strftime('%Y-%m-%d')}
        for _, row in recent.iterrows()
    ]

    # Summary statistics
    summary = {
        'total_events': len(df),
        'unique_items': df['title'].nunique(),
        'date_range': f"{df['timestamp'].min():%b %Y} - {df['timestamp'].max():%b %Y}",
    }

    return {
        'sample_titles': unique_titles,
        'recent_events': recent_events,
        'summary': summary,
    }
```

### Category/Topic Aggregation

```python
def aggregate_interests(df, tag_column='tags', top_n=30):
    """Aggregate and rank interests from tag data."""

    all_tags = Counter()
    for tags_str in df[tag_column]:
        tags = parse_tags(tags_str)  # See data-analysis skill
        all_tags.update(tags)

    # Return as ranked list with counts
    return [
        {'topic': topic, 'count': count}
        for topic, count in all_tags.most_common(top_n)
    ]
```

## Prompt Templates

### Narrative Generation (Haiku/Sonnet)

```python
narrative_prompt = f"""Based on this user's reading activity, write a warm, personalized narrative.

User: {user_name}
Location: {location}
Time Period: {date_range}

Activity Summary:
- Total articles read: {total_events}
- Unique articles: {unique_items}
- Top interests: {top_interests}

Sample of titles they engaged with:
{titles_list}

Write a 3-4 paragraph story about their reading journey. Be specific, reference actual topics they read about. Tone should be warm and celebratory."""
```

### Structured Analysis (GPT/Haiku)

```python
analysis_prompt = f"""Analyze this user's interests based on their reading data.

Data:
{json.dumps(context, indent=2)}

Return a JSON object with:
{{
  "core_interests": [
    {{"topic": "...", "strength": "high/medium", "evidence": "..."}}
  ],
  "casual_interests": [
    {{"topic": "...", "strength": "low", "evidence": "..."}}
  ],
  "emerging_interests": [
    {{"topic": "...", "trend": "growing", "evidence": "..."}}
  ]
}}

Only include interests with clear evidence from the data."""
```

## Response Parsing

### JSON Response Cleaning

```python
import re
import json

def clean_json_response(response_text):
    """Extract and parse JSON from LLM response."""

    # Remove markdown code fences
    cleaned = re.sub(r'```json\s*', '', response_text)
    cleaned = re.sub(r'```\s*', '', cleaned)
    cleaned = cleaned.strip()

    # Try to parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object in response
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            return json.loads(match.group())
        return None
```

### Markdown to HTML Conversion

```python
import re

def markdown_to_html(text):
    """Convert basic markdown to HTML."""

    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

    # Bullet points
    lines = text.split('\n')
    in_list = False
    result = []

    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)

    if in_list:
        result.append('</ul>')

    # Paragraphs
    text = '\n'.join(result)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = f'<p>{text}</p>'

    return text
```

## Model Selection Guidelines

| Use Case | Recommended Model | Token Limit | Temperature |
|----------|------------------|-------------|-------------|
| Warm narratives | Haiku 4.5 / Sonnet | 2000-4000 | 0.7 |
| Structured JSON | Haiku 4.5 / GPT-5-nano | 500-1000 | 0.3 |
| Short summaries | Haiku 4.5 | 200-500 | 0.5 |
| Creative descriptions | Sonnet / Opus | 1000-2000 | 0.8 |

## Error Handling

```python
def safe_llm_call(prompt, model, max_retries=2):
    """LLM call with graceful fallback."""

    for attempt in range(max_retries + 1):
        try:
            response = call_llm(prompt, model)

            # Validate response
            if not response or len(response) < 10:
                raise ValueError("Empty or too short response")

            return response

        except Exception as e:
            if attempt == max_retries:
                # Return fallback content
                return generate_fallback_content()
            continue
```
