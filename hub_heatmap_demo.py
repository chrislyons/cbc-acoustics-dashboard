#!/usr/bin/env python3
"""
Demonstration script to show The Hub RT60 heatmap functionality
Compares Hub and Studio 8 heatmaps side by side
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from rt60_heatmap_analyzer_hub import RT60HeatmapAnalyzerHub
from rt60_heatmap_analyzer_fixed import RT60HeatmapAnalyzer

def create_comparison_heatmaps(hub_panels=10, studio8_panels=25):
    """Create side-by-side comparison of Hub and Studio 8 heatmaps"""
    
    # Initialize analyzers
    hub_analyzer = RT60HeatmapAnalyzerHub()
    studio8_analyzer = RT60HeatmapAnalyzer()
    
    # Create individual heatmaps
    hub_fig = hub_analyzer.create_rt60_heatmap(panel_count=hub_panels)
    studio8_fig = studio8_analyzer.create_rt60_heatmap(panel_count=studio8_panels)
    
    # Extract data from the individual figures
    hub_heatmap = hub_fig.data[0]
    studio8_heatmap = studio8_fig.data[0]
    
    # Create subplot figure
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=[
            f"The Hub - RT60 Heatmap ({hub_panels} panels)",
            f"Studio 8 - RT60 Heatmap ({studio8_panels} panels)"
        ],
        horizontal_spacing=0.15
    )
    
    # Add Hub heatmap (left)
    fig.add_trace(
        go.Heatmap(
            z=hub_heatmap.z,
            x=hub_heatmap.x,
            y=hub_heatmap.y,
            colorscale=hub_heatmap.colorscale,
            zmin=hub_heatmap.zmin,
            zmax=hub_heatmap.zmax,
            hovertemplate=hub_heatmap.hovertemplate,
            hovertext=hub_heatmap.hovertext,
            colorbar=dict(
                title="RT60 (seconds)",
                x=0.42,  # Position colorbar for left plot
                len=0.9
            )
        ),
        row=1, col=1
    )
    
    # Add Studio 8 heatmap (right)
    fig.add_trace(
        go.Heatmap(
            z=studio8_heatmap.z,
            x=studio8_heatmap.x,
            y=studio8_heatmap.y,
            colorscale=studio8_heatmap.colorscale,
            zmin=studio8_heatmap.zmin,
            zmax=studio8_heatmap.zmax,
            hovertemplate=studio8_heatmap.hovertemplate,
            hovertext=studio8_heatmap.hovertext,
            colorbar=dict(
                title="RT60 (seconds)",
                x=1.0,   # Position colorbar for right plot
                len=0.9
            )
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title="RT60 Heatmap Comparison: The Hub vs Studio 8",
        height=500,
        font=dict(size=11),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    # Update x-axis labels
    fig.update_xaxes(title_text="Measurement Position", row=1, col=1)
    fig.update_xaxes(title_text="Measurement Position", row=1, col=2)
    
    # Update y-axis labels
    fig.update_yaxes(title_text="Frequency Band", row=1, col=1)
    fig.update_yaxes(title_text="", row=1, col=2)  # No label on right to avoid duplication
    
    return fig

def show_hub_data_summary():
    """Display summary of The Hub data"""
    analyzer = RT60HeatmapAnalyzerHub()
    
    print("=" * 60)
    print("THE HUB - RT60 ANALYSIS SUMMARY")
    print("=" * 60)
    print()
    
    if analyzer.actual_rt60_data:
        print("📊 MEASUREMENT POSITIONS:")
        for pos, data in analyzer.actual_rt60_data.items():
            if data:
                avg_rt60 = sum(data.values()) / len(data)
                min_rt60 = min(data.values())
                max_rt60 = max(data.values())
                coords = analyzer.measurement_positions[pos]['coords']
                
                print(f"  {analyzer.measurement_positions[pos]['name']:15s}")
                print(f"    • Position: ({coords[0]:4.1f}, {coords[1]:4.1f}, {coords[2]:4.1f}) feet")
                print(f"    • RT60 Range: {min_rt60:.2f}s - {max_rt60:.2f}s")
                print(f"    • Average RT60: {avg_rt60:.2f}s")
                
                # Show frequency breakdown
                print(f"    • Frequencies: ", end="")
                for freq, rt60 in sorted(data.items()):
                    freq_label = f"{freq//1000}kHz" if freq >= 1000 else f"{freq}Hz"
                    color = "🟢" if rt60 <= 0.4 else "🟡" if rt60 <= 0.5 else "🔴"
                    print(f"{freq_label}:{color}{rt60:.2f}s ", end="")
                print()
                print()
    
    print("🎯 TREATMENT RECOMMENDATIONS:")
    print("  • The Hub is smaller than Studio 8, so fewer panels needed")
    print("  • Current RT60 values are generally good (0.33s - 0.59s)")
    print("  • CeilingCorner position needs most attention (0.59s)")
    print("  • Chair1 position already excellent (0.33s)")
    print("  • Recommended: 10-15 panels for optimal treatment")
    print()

if __name__ == "__main__":
    print("🚀 Hub RT60 Heatmap Demo")
    print()
    
    # Show data summary first
    show_hub_data_summary()
    
    # Test different panel scenarios
    scenarios = [
        {"hub": 0, "studio8": 0, "desc": "No Treatment"},
        {"hub": 5, "studio8": 10, "desc": "Light Treatment"},
        {"hub": 10, "studio8": 25, "desc": "Recommended Treatment"},
        {"hub": 15, "studio8": 40, "desc": "Maximum Treatment"}
    ]
    
    print("📈 RT60 IMPROVEMENT SCENARIOS:")
    print()
    
    hub_analyzer = RT60HeatmapAnalyzerHub()
    studio8_analyzer = RT60HeatmapAnalyzer()
    
    for scenario in scenarios:
        # Calculate Hub metrics
        hub_rt60_data = hub_analyzer.calculate_rt60_with_panels(scenario["hub"])
        hub_values = []
        for pos_data in hub_rt60_data.values():
            hub_values.extend(pos_data.values())
        hub_avg = sum(hub_values) / len(hub_values)
        
        # Calculate Studio 8 metrics
        studio8_rt60_data = studio8_analyzer.calculate_rt60_with_panels(scenario["studio8"])
        studio8_values = []
        for pos_data in studio8_rt60_data.values():
            studio8_values.extend(pos_data.values())
        studio8_avg = sum(studio8_values) / len(studio8_values)
        
        print(f"  {scenario['desc']:20s}")
        print(f"    Hub ({scenario['hub']:2d} panels):     {hub_avg:.2f}s average RT60")
        print(f"    Studio 8 ({scenario['studio8']:2d} panels): {studio8_avg:.2f}s average RT60")
        print()
    
    print("🎨 Creating comparison heatmap...")
    comparison_fig = create_comparison_heatmaps(hub_panels=10, studio8_panels=25)
    
    # Save the comparison figure (optional)
    comparison_fig.write_html("hub_studio8_rt60_comparison.html")
    print("✅ Comparison heatmap saved as 'hub_studio8_rt60_comparison.html'")
    
    print()
    print("🔧 Individual heatmaps can be generated using:")
    print("  • hub_analyzer.create_rt60_heatmap(panel_count=10)")
    print("  • Combined 3D visualization: hub_analyzer.create_hub_3d_heatmap_overlay(panel_count=10)")
    print()
    print("✨ The Hub RT60 heatmap analyzer is ready for use!")