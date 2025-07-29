# CBC Dashboard UI Enhancement Plan

## Overview
Transform the CBC Acoustic Dashboard to match the sophisticated dark theme aesthetic of Treble.tech while fixing the current dark mode readability issues and migrating all styling to a unified external stylesheet.

## Phase 1: Design System Development

### 1.1 Create New Unified Stylesheet (dashboard_styles_v2.css)
- **Color Palette Enhancement**
  - Dark theme primary: #0a0e1a (deeper than current)
  - Dark secondary: #141824
  - Emerald accent: #10b981 (Treble-inspired green)
  - Secondary accent: #3b82f6 (modern blue)
  - Text hierarchy: #f9fafb, #e5e7eb, #9ca3af
  - Success/Warning/Error states with proper contrast

### 1.2 Typography Overhaul
- **Font Stack**: Inter, -apple-system, BlinkMacSystemFont (modern, clean)
- **Size Scale**: Implement modular scale (1.25 ratio)
- **Weight Hierarchy**: 300, 400, 500, 600, 700
- **Letter spacing**: Tighter for headings, looser for body text

### 1.3 Component Styling
- **Cards**: Glassmorphic effect with subtle backdrop blur
- **Buttons**: Gradient borders with hover glow effects
- **Charts**: Dark theme with neon accents for data visualization
- **Sidebar**: Semi-transparent with blur effect
- **Headers**: Gradient text effects for impact

## Phase 2: CSS Architecture Migration

### 2.1 Remove Inline Styles from Python Files
- Extract all CSS from cbc8_acoustic_dashboard.py
- Remove style definitions from visualization components
- Create CSS classes for all styled elements

### 2.2 Implement CSS Variables System
- Define comprehensive variable set for all colors, spacing, typography
- Create light/dark theme switching capability
- Add CSS custom properties for dynamic theming

### 2.3 Create Component Library
- `.card`, `.card--metric`, `.card--highlight`
- `.btn`, `.btn--primary`, `.btn--secondary`
- `.chart-container`, `.visualization-wrapper`
- `.sidebar`, `.header`, `.footer`

## Phase 3: Dark Mode Excellence

### 3.1 Fix Text Visibility Issues
- Remove opacity modifiers that reduce contrast
- Implement proper color contrast ratios (WCAG AAA)
- Add text shadows for enhanced readability
- Create inverted color schemes for highlights

### 3.2 Chart Theme Integration
- Configure Plotly dark theme templates
- Custom color scales matching design system
- Consistent hover states and tooltips

## Phase 4: Modern UI Enhancements

### 4.1 Micro-interactions
- Subtle hover animations (scale, glow)
- Smooth transitions (0.2s ease-out)
- Loading states with skeleton screens
- Progress indicators with gradient fills

### 4.2 Visual Effects
- Gradient overlays for depth
- Box shadows with color tints
- Border gradients for active states
- Backdrop filters for modern glass effect

### 4.3 Layout Improvements
- CSS Grid for responsive layouts
- Flexbox for component alignment
- Container queries for adaptive components
- Proper spacing rhythm (8px base unit)

## Phase 5: Implementation Details

### 5.1 File Structure
```
assets/
├── css/
│   ├── dashboard_styles_v2.css (main stylesheet)
│   ├── components.css (reusable components)
│   ├── themes.css (theme variables)
│   └── utilities.css (utility classes)
└── fonts/
    └── Inter/ (if self-hosting fonts)
```

### 5.2 Python Code Updates
- Update cbc8_acoustic_dashboard.py to load external CSS
- Remove DASHBOARD_CSS constant
- Add CSS file linking in st.markdown
- Implement theme detection and class application

### 5.3 Launch Script Updates
- Ensure CSS files are served correctly
- Add cache busting for CSS updates
- Configure proper MIME types

## Phase 6: Specific Improvements

### 6.1 Header Redesign
- Dark gradient background with noise texture
- Glowing text effect for title
- Animated gradient border
- Floating particles background (CSS only)

### 6.2 Metric Cards
- Dark glass morphism effect
- Neon accent left border
- Hover: Slight lift with glow
- Icon integration with gradient fills

### 6.3 Sidebar Enhancement
- Semi-transparent dark background
- Blur effect for content behind
- Neon accent for active items
- Smooth hover transitions

### 6.4 Chart Containers
- Dark bordered containers
- Subtle inner glow
- Consistent padding and margins
- Responsive sizing

## Expected Outcomes
1. **Professional Aesthetic**: Match Treble.tech's sophisticated dark theme
2. **Fixed Dark Mode**: All text fully readable in dark mode
3. **Unified Styling**: All styles in external CSS files
4. **Modern Typography**: Clean, hierarchical font system
5. **Enhanced UX**: Smooth interactions and visual feedback
6. **Maintainable Code**: Separated concerns, reusable components
7. **Performance**: Optimized CSS with minimal redundancy

This plan will transform your dashboard into a modern, professional tool that rivals industry-leading acoustic software interfaces while maintaining excellent usability and readability.