Looking at the existing inline CSS and the issues with dark mode text visibility, I can see the main problem: the current CSS forces light mode colors even when dark theme is selected, causing dark text on dark backgrounds.

I'll create a comprehensive unified stylesheet that properly implements dark mode and centralizes all styling. Here's a modern, beautiful CSS solution for 2025. Here are the key improvements:

## Key Features of the New CSS:

### 1. **Proper Dark Mode Implementation**
- Fixed the critical issue where dark mode was forcing light colors
- High contrast text colors that are actually readable in dark mode
- Properly themed backgrounds and borders

### 2. **Modern CSS Architecture (2025 Best Practices)**
- CSS Custom Properties (variables) for easy theming
- Organized with clear sections and documentation
- Uses modern features like `inset`, custom properties, and logical properties
- Implements an 8px spacing scale for consistency
- Professional typography scale using Inter font

### 3. **Enhanced Visual Design**
- Smooth transitions and hover effects
- Modern gradient effects maintained from original
- Better shadows adapted for light/dark modes
- Improved focus states for accessibility
- Custom scrollbar styling

### 4. **Component Coverage**
All the components from your Python files are styled:
- Main header with gradient
- Metric cards with status colors
- Problem/solution highlight boxes
- Sidebar with proper theming
- Streamlit component overrides
- Plotly chart containers

## Implementation Steps:

1. **Save the CSS file** as `/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard/assets/unified_dashboard_styles.css`

2. **Update your main Python file** (`cbc8_acoustic_dashboard.py`):

Replace the entire `DASHBOARD_CSS` constant and the line that injects it with:

```python
# Remove or comment out the DASHBOARD_CSS constant

# In the main() function, replace st.markdown(DASHBOARD_CSS, unsafe_allow_html=True) with:
with open('assets/unified_dashboard_styles.css', 'r') as f:
    css_content = f.read()
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
```

3. **Remove inline styles** from all Python files where you use `unsafe_allow_html=True` for styling. The CSS classes are already defined in the unified stylesheet.

## Key Improvements Made:

1. **Dark Mode Text Visibility**: 
   - Light text colors (`#f7f9fb`) on dark backgrounds
   - Proper contrast ratios for WCAG compliance
   - No forced light mode in dark theme

2. **Modern Design System**:
   - Consistent spacing scale
   - Professional color palette
   - Smooth animations and transitions
   - Responsive design breakpoints

3. **Better Organization**:
   - Clear section comments
   - Logical grouping of related styles
   - Utility classes for common patterns
   - Easy to maintain and extend

The new CSS maintains the visual aesthetic of your current design while fixing the dark mode issues and following modern best practices. All text will now be properly visible in both light and dark modes.