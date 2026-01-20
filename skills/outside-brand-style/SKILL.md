---
name: outside-brand-style
description: Apply Outside brand visual styling with signature yellow, black, and white color scheme. Use when creating reports, dashboards, HTML pages, or visualizations that need Outside magazine brand aesthetics. Triggers on requests for Outside branding, Outside style, or yellow/black color schemes.
---

# Outside Brand Style

Apply Outside magazine's distinctive visual identity featuring bold yellow (#FFD100), black, and white. Use for reports, dashboards, and data visualizations.

## Color Palette

### CSS Custom Properties
```css
:root {
    /* Primary - Signature Outside Yellow */
    --primary: #FFD100;
    --primary-dark: #E6BC00;
    --primary-light: #FFF3B0;

    /* Secondary - Black */
    --secondary: #000000;
    --secondary-light: #1a1a1a;

    /* Neutrals */
    --accent: #333333;
    --text: #000000;
    --text-light: #555555;
    --text-muted: #666666;

    /* Backgrounds */
    --bg: #F7F7F7;
    --bg-dark: #000000;
    --card-bg: #FFFFFF;

    /* Borders & Shadows */
    --border: #E0E0E0;
    --shadow-light: 0 2px 10px rgba(0,0,0,0.08);
    --shadow-hover: 0 8px 25px rgba(0,0,0,0.15);
}
```

### Chart.js Colors
```javascript
const chartColors = [
    '#FFD100',  // Primary yellow
    '#000000',  // Black
    '#333333',  // Dark gray
    '#666666',  // Medium gray
    '#999999',  // Light gray
    '#CCCCCC',  // Lighter gray
    '#E6BC00',  // Dark gold
    '#B8960A'   // Bronze
];
```

## Typography

```css
body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    color: var(--text);
}

h1, h2, h3 {
    font-weight: 700;
    line-height: 1.2;
}

h1 { font-size: 2.5rem; }
h2 { font-size: 1.8rem; }
h3 { font-size: 1.3rem; }
```

## Component Patterns

### Hero Section (Dark Background)
```css
.hero {
    background: var(--secondary);
    color: white;
    padding: 60px 40px;
    text-align: center;
}

.hero h1 {
    color: var(--primary);
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.hero .subtitle {
    color: rgba(255,255,255,0.9);
    font-size: 1.2rem;
}
```

### Cards (Light Background)
```css
.card {
    background: var(--card-bg);
    border-radius: 16px;
    padding: 25px;
    box-shadow: var(--shadow-light);
    transition: all 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-hover);
}

.card h3 {
    color: var(--secondary);
    border-bottom: 3px solid var(--primary);
    padding-bottom: 10px;
    margin-bottom: 15px;
}
```

### Stat Cards
```css
.stat-card {
    text-align: center;
    padding: 30px 20px;
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--secondary);
    text-shadow: 2px 2px 0 var(--primary);
}

.stat-label {
    color: var(--text-light);
    font-size: 0.9rem;
    margin-top: 5px;
}
```

### Tags/Badges
```css
.tag {
    display: inline-block;
    background: var(--primary);
    color: var(--secondary);
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}

.tag-dark {
    background: var(--secondary);
    color: var(--primary);
}
```

### Spotlight Section (Featured Content)
```css
.spotlight {
    background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
    color: white;
    padding: 40px;
    border-radius: 16px;
}

.spotlight h2 {
    color: var(--primary);
    margin-bottom: 20px;
}

.spotlight-highlight {
    border-left: 4px solid var(--primary);
    padding-left: 20px;
    margin: 20px 0;
}
```

### Interest Cards (Two Variants)
```css
/* Core interests - warm highlight */
.interest-core {
    background: #fffbea;
    border-left: 4px solid var(--primary);
    padding: 20px;
    border-radius: 0 12px 12px 0;
}

/* Casual interests - neutral */
.interest-casual {
    background: white;
    border-left: 4px solid var(--accent);
    padding: 20px;
    border-radius: 0 12px 12px 0;
}

.interest-strength {
    background: var(--primary);
    color: var(--secondary);
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}
```

### Platform/Ecosystem Cards
```css
.platform-card {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: white;
    padding: 25px;
    border-radius: 12px;
    border-top: 3px solid var(--primary);
}

/* Platform-specific accent colors */
.platform-editorial { border-top-color: #FFD100; }
.platform-trailforks { border-top-color: #4CAF50; }
.platform-gaia { border-top-color: #2196F3; }
.platform-watch { border-top-color: #FF5722; }
.platform-app { border-top-color: #9C27B0; }
```

## Responsive Grid

```css
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 25px;
}

@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .hero {
        padding: 40px 20px;
    }

    .hero h1 {
        font-size: 1.8rem;
    }
}
```

## Chart.js Configuration

### Line Chart (Activity Over Time)
```javascript
{
    type: 'line',
    data: {
        datasets: [{
            borderColor: '#FFD100',
            backgroundColor: 'rgba(255, 209, 0, 0.15)',
            pointBackgroundColor: '#000000',
            pointBorderColor: '#FFD100',
            pointRadius: 5,
            pointHoverRadius: 7,
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        plugins: {
            legend: { display: false }
        },
        scales: {
            y: { beginAtZero: true }
        }
    }
}
```

### Bar Chart
```javascript
{
    type: 'bar',
    data: {
        datasets: [{
            backgroundColor: '#FFD100',
            borderColor: '#E6BC00',
            borderWidth: 1,
            borderRadius: 4
        }]
    }
}
```

### Doughnut Chart
```javascript
{
    type: 'doughnut',
    data: {
        datasets: [{
            backgroundColor: chartColors,
            borderColor: '#FFFFFF',
            borderWidth: 2
        }]
    },
    options: {
        plugins: {
            legend: {
                position: 'right',
                labels: { padding: 15 }
            }
        }
    }
}
```

## HTML Report Template

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Report Title</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Include CSS custom properties and components */
    </style>
</head>
<body>
    <!-- Hero -->
    <section class="hero">
        <div class="emoji-avatar">🏔️</div>
        <h1>Report Title</h1>
        <p class="subtitle">Date Range • Key Metric</p>
    </section>

    <!-- Stats Grid -->
    <section class="container">
        <div class="grid">
            <div class="card stat-card">
                <div class="stat-number">1,234</div>
                <div class="stat-label">Total Events</div>
            </div>
            <!-- More stat cards -->
        </div>
    </section>

    <!-- Content Sections -->
    <section class="container">
        <div class="card">
            <h3>Section Title</h3>
            <!-- Content -->
        </div>
    </section>

    <!-- Footer -->
    <footer>
        <p>Generated on <span id="date"></span></p>
    </footer>
</body>
</html>
```

## Bundled Resources

- [references/color-usage.md](references/color-usage.md) - When to use each color
- [references/chart-templates.md](references/chart-templates.md) - Full Chart.js configurations
- [assets/outside-palette.css](assets/outside-palette.css) - Complete CSS file

## Quick Reference

| Element | Background | Text/Border | Notes |
|---------|------------|-------------|-------|
| Hero | Black | Yellow title, white text | |
| Cards | White | Black headings | Yellow underline |
| Tags | Yellow | Black | Rounded (20px) |
| Stats | White | Black with yellow shadow | |
| Spotlight | Black gradient | Yellow headings, white text | |
| Charts | - | Yellow primary, black secondary | |
