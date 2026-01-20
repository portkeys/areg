# Outside Brand Color Usage Guide

When to use each color in the Outside brand palette.

## Primary Yellow (#FFD100)

**The signature Outside color.** Use for:

- Hero section titles on dark backgrounds
- Section heading underlines/accents
- Interactive element hover states
- Tags and badges (background)
- Chart primary data series
- Call-to-action buttons
- Border accents (left borders, top borders)
- Text shadows on stat numbers

**Don't use:**
- As body text color (poor contrast)
- Large background areas on light pages
- Subtle UI elements (too attention-grabbing)

## Black (#000000)

**Anchoring color for authority and contrast.** Use for:

- Hero section backgrounds
- Primary body text
- Card headings
- Stat numbers (with yellow shadow)
- Chart secondary data series
- Tag text on yellow backgrounds

**Don't use:**
- As the only color (needs yellow accent)
- Text on dark backgrounds (use white)

## White (#FFFFFF)

**Clean, professional foundation.** Use for:

- Card backgrounds
- Body text on dark backgrounds
- Chart segment borders
- Negative space

## Gray Scale

### Dark Gray (#333333)
- Subtext and secondary headings
- Borders and dividers
- Chart tertiary series

### Medium Gray (#555555, #666666)
- Muted text (labels, metadata)
- Less important information
- Placeholder text

### Light Gray (#F7F7F7)
- Page backgrounds
- Alternating row backgrounds
- Disabled states

## Platform-Specific Accents

For multi-platform ecosystems, use these accent colors for visual differentiation:

| Platform | Color | Hex |
|----------|-------|-----|
| Editorial/Core | Yellow | #FFD100 |
| Outdoor/Trails | Green | #4CAF50 |
| GPS/Maps | Blue | #2196F3 |
| Video/Watch | Orange | #FF5722 |
| Mobile App | Purple | #9C27B0 |

## Color Combinations

### High Contrast (Hero sections)
- Background: Black
- Primary text: Yellow
- Secondary text: White

### Standard (Cards, content)
- Background: White
- Primary text: Black
- Accent: Yellow (borders, underlines)

### Warm Highlight (Featured content)
- Background: #fffbea (cream)
- Border: Yellow
- Text: Black

### Dark Gradient (Spotlight sections)
```css
background: linear-gradient(135deg, #000 0%, #1a1a1a 100%);
```

## Accessibility Notes

- Yellow (#FFD100) on white fails WCAG contrast requirements
- Always use black text on yellow backgrounds
- Yellow works well as borders/accents on white
- Use white text on black backgrounds
- Gray text (#555) on white has acceptable contrast
