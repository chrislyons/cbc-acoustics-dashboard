#!/usr/bin/env python3
"""
Advanced Acoustic Treatment Simulator
Real-time before/after comparison with interactive panel placement
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import json

class TreatmentSimulator:
    def __init__(self):
        self.base_path = Path('/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard')
        
        # Load default space data (will be updated in render method)
        self._load_space_parameters("Studio 8")
        
        # Panel specifications
        self.panel_specs = {
            "2_inch": {
                "size": 8,  # square feet (2'x4')
                "nrc": 0.80,
                "cost": 20,
                "absorption_curve": self._get_absorption_curve("2_inch")
            },
            "3_inch": {
                "size": 8,  # square feet (2'x4')
                "nrc": 0.95,
                "cost": 25,
                "absorption_curve": self._get_absorption_curve("3_inch")
            },
            "5_5_inch": {
                "size": 8,  # square feet (2'x4')
                "nrc": 1.15,
                "cost": 30,
                "absorption_curve": self._get_absorption_curve("5_5_inch")
            }
        }
        
        # Current room conditions (from analysis)
        self.current_conditions = {
            "rt60_by_freq": {
                125: 0.85, 250: 0.92, 500: 0.78, 1000: 0.71, 2000: 0.68, 4000: 0.55
            },
            "sti_by_position": {
                "Host A (Reference)": 0.95,
                "Host C (Talent)": 0.67,
                "Mid Room": 0.71,
                "NE Corner": 0.58,
                "SE Corner": 0.62,
                "Ceiling": 0.64
            },
            "average_sti": 0.67,
            "average_rt60": 0.75
        }
        
        # Target conditions
        self.target_conditions = {
            "rt60_target": 0.4,
            "sti_target": 0.75,
            "rt60_range": [0.3, 0.5]
        }
    
    def _load_drape_data(self, space="Studio 8"):
        """Load drape compensation data from CSV file"""
        try:
            # Determine space-specific file
            space_id = "Studio8" if space == "Studio 8" else "TheHub"
            drape_file = self.base_path / f"data/generated/250728-{space_id}-Drape_Compensation_Evidence.csv"
            if drape_file.exists():
                drape_df = pd.read_csv(drape_file)
                # Convert to dictionary format for easy lookup
                drape_absorption = {}
                for _, row in drape_df.iterrows():
                    freq = int(row['frequency_hz'])
                    absorption_coeff = float(row['drape_absorption_coeff'])
                    drape_absorption[freq] = absorption_coeff
                return drape_absorption
            else:
                # Fallback to hardcoded values if CSV not found
                return {
                    125: 0.15, 250: 0.30, 500: 0.55, 1000: 0.75, 2000: 0.80, 4000: 0.70
                }
        except Exception as e:
            # Fallback to hardcoded values if there's an error
            print(f"Warning: Could not load drape data from CSV ({e}), using fallback values")
            return {
                125: 0.15, 250: 0.30, 500: 0.55, 1000: 0.75, 2000: 0.80, 4000: 0.70
            }
    
    def _calculate_equivalent_panels(self):
        """Calculate equivalent panels needed to compensate for drape removal"""
        drape_absorption = self.drape_data
        
        # Average drape size/impact (40 square feet estimated)
        drape_size = 40  # square feet
        
        # Calculate equivalent panels for each thickness
        equivalents = {}
        
        for thickness, panel_spec in self.panel_specs.items():
            panel_absorption = panel_spec["absorption_curve"]
            panel_size = panel_spec["size"]  # 8 sq ft per panel
            
            # Calculate average absorption loss from drape removal
            avg_drape_absorption = sum(drape_absorption.values()) / len(drape_absorption)
            avg_panel_absorption = sum(panel_absorption.values()) / len(panel_absorption)
            
            # Calculate equivalent panels: (drape_size * avg_drape_absorption) / (panel_size * avg_panel_absorption)
            equivalent_panels = (drape_size * avg_drape_absorption) / (panel_size * avg_panel_absorption)
            
            equivalents[thickness] = {
                "count": round(equivalent_panels, 1),
                "cost": round(equivalent_panels * panel_spec["cost"], 0)
            }
        
        return equivalents
    
    def _load_space_parameters(self, space="Studio 8"):
        """Load space-specific room parameters and RT60 data"""
        if space == "The Hub":
            # The Hub parameters (hexagonal space)
            self.room_volume = 1900  # cubic feet (estimated)
            self.room_surface_area = 1400  # square feet (estimated)
            
            # The Hub RT60 data (different acoustic characteristics)
            self.current_conditions = {
                "rt60_by_freq": {
                    125: 0.72, 250: 0.78, 500: 0.65, 1000: 0.58, 2000: 0.52, 4000: 0.48
                },
                "sti_by_position": {
                    "Back Corner": 0.73,
                    "Ceiling Corner": 0.68,
                    "Chair 1": 0.75,
                    "Chair 2": 0.71,
                    "Mid Room": 0.69
                },
                "average_sti": 0.71,
                "average_rt60": 0.62
            }
        else:
            # Studio 8 parameters (default)
            self.room_volume = 2650  # cubic feet
            self.room_surface_area = 1847  # square feet
            
            # Studio 8 RT60 data (from analysis)
            self.current_conditions = {
                "rt60_by_freq": {
                    125: 0.85, 250: 0.92, 500: 0.78, 1000: 0.71, 2000: 0.68, 4000: 0.55
                },
                "sti_by_position": {
                    "Host A (Reference)": 0.95,
                    "Host C (Talent)": 0.67,
                    "Mid Room": 0.71,
                    "NE Corner": 0.58,
                    "SE Corner": 0.62,
                    "Ceiling": 0.64
                },
                "average_sti": 0.67,
                "average_rt60": 0.75
            }
    
    
    def _get_absorption_curve(self, thickness):
        """Get frequency-dependent absorption coefficients"""
        if thickness == "2_inch":
            return {
                125: 0.15, 250: 0.40, 500: 0.75, 1000: 0.80, 2000: 0.85, 4000: 0.85
            }
        elif thickness == "3_inch":
            return {
                125: 0.25, 250: 0.60, 500: 0.90, 1000: 0.95, 2000: 0.98, 4000: 0.98
            }
        else:  # 5.5_inch
            return {
                125: 0.45, 250: 0.80, 500: 1.05, 1000: 1.15, 2000: 1.18, 4000: 1.15
            }
    
    def calculate_rt60_with_panels(self, panel_counts, drape_removal=True):
        """Calculate RT60 with added absorption panels using Sabine equation
        
        Args:
            panel_counts: Dict with thickness keys and count values, e.g. {'2_inch': 4, '3_inch': 8, '5_5_inch': 4}
            drape_removal: Whether to account for drape removal
        """
        
        # Current absorption (estimated from RT60)
        current_absorption = {}
        for freq, rt60 in self.current_conditions["rt60_by_freq"].items():
            # RT60 = 0.161 * V / (S * α)
            current_absorption[freq] = (0.161 * self.room_volume) / (rt60 * self.room_surface_area)
        
        # Calculate total added absorption from all panel types
        total_added_absorption = {freq: 0 for freq in current_absorption.keys()}
        
        for thickness, count in panel_counts.items():
            if count > 0:
                panel_spec = self.panel_specs[thickness]
                panel_absorption = panel_spec["absorption_curve"]
                
                for freq in current_absorption.keys():
                    added_absorption = count * panel_spec["size"] * panel_absorption[freq] / self.room_surface_area
                    total_added_absorption[freq] += added_absorption
        
        # Drape compensation (if removing 30-40 lb velvet) - using CSV data
        drape_absorption = self.drape_data if drape_removal else {}
        
        # Calculate new RT60 values
        new_rt60 = {}
        for freq in current_absorption.keys():
            # Subtract drape absorption if removing
            drape_loss = drape_absorption.get(freq, 0) * 40 / self.room_surface_area if drape_removal else 0
            
            # New total absorption coefficient
            new_alpha = current_absorption[freq] + total_added_absorption[freq] - drape_loss
            new_alpha = max(0.01, min(0.99, new_alpha))  # Clamp to realistic range
            
            # New RT60
            new_rt60[freq] = (0.161 * self.room_volume) / (new_alpha * self.room_surface_area)
        
        return new_rt60
    
    def calculate_sti_improvement(self, rt60_improvement):
        """Estimate STI improvement based on RT60 reduction"""
        
        # Empirical relationship: STI improves as RT60 approaches target
        current_sti = self.current_conditions["average_sti"]
        target_sti = self.target_conditions["sti_target"]
        
        # RT60 improvement factor (0 to 1)
        rt60_factor = min(1.0, rt60_improvement / 0.3)  # Normalize to 0.3s improvement
        
        # STI improvement (conservative estimate)
        sti_improvement = rt60_factor * (target_sti - current_sti) * 0.7  # 70% of theoretical max
        
        return min(target_sti, current_sti + sti_improvement)
    
    def create_before_after_comparison(self, panel_counts, drape_removal):
        """Create sexy EQ-style curve comparison chart with richer frequency data"""
        
        # Calculate predictions
        new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
        
        # Get total panel count for display
        total_panels = sum(panel_counts.values())
        
        # Create richer frequency data for smooth EQ curves (30 Hz to 3 kHz)
        extended_freqs = [30, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 
                         630, 800, 1000, 1250, 1600, 2000, 2500, 3000]
        
        # Interpolate current conditions to extended frequency range
        current_freqs = list(self.current_conditions["rt60_by_freq"].keys())
        current_rt60_values = list(self.current_conditions["rt60_by_freq"].values())
        
        # Create smooth interpolated curves with spline-like smoothing
        import numpy as np
        
        # Use cubic spline interpolation for smoother curves (if scipy available)
        try:
            from scipy.interpolate import interp1d
            current_interp = interp1d(current_freqs, current_rt60_values, kind='cubic', 
                                    bounds_error=False, fill_value='extrapolate')
            current_smooth = current_interp(extended_freqs)
        except ImportError:
            # Fallback to linear interpolation if scipy not available
            current_smooth = np.interp(extended_freqs, current_freqs, current_rt60_values)
        
        # Calculate treated values for extended frequency range with smooth interpolation
        treated_rt60_values = [new_rt60[f] for f in current_freqs]
        try:
            from scipy.interpolate import interp1d
            treated_interp = interp1d(current_freqs, treated_rt60_values, kind='cubic',
                                    bounds_error=False, fill_value='extrapolate')
            treated_smooth = treated_interp(extended_freqs)
        except ImportError:
            # Fallback to linear interpolation if scipy not available
            treated_smooth = np.interp(extended_freqs, current_freqs, treated_rt60_values)
        
        # Target values with some realistic variation
        target_base = self.target_conditions["rt60_target"]
        target_smooth = [target_base + 0.05 * np.sin(np.log10(f/125) * 2) for f in extended_freqs]
        
        fig = go.Figure()
        
        # Target range band (fill area first, so it's behind curves)
        target_upper = [t + 0.05 for t in target_smooth]
        target_lower = [max(0.25, t - 0.05) for t in target_smooth]
        
        fig.add_trace(go.Scatter(
            x=extended_freqs + extended_freqs[::-1],
            y=target_upper + target_lower[::-1],
            fill='toself',
            fillcolor='rgba(39, 174, 96, 0.15)',
            line=dict(color='rgba(39, 174, 96, 0)'),
            name='Target Zone',
            hoverinfo='skip',
            showlegend=True
        ))
        
        # Current RT60 curve (problem areas) - smooth red curve
        fig.add_trace(go.Scatter(
            x=extended_freqs,
            y=current_smooth,
            mode='lines',
            name='Current RT60',
            line=dict(color='#e74c3c', width=4, smoothing=0.5),
            fill='tonexty',
            fillcolor='rgba(231, 76, 60, 0.1)',
            hovertemplate="<b>Current RT60</b><br>Frequency: %{x} Hz<br>RT60: %{y:.2f}s<br><i>Excessive reverberation</i><extra></extra>"
        ))
        
        # Treated RT60 curve (solution) - smooth blue curve
        fig.add_trace(go.Scatter(
            x=extended_freqs,
            y=treated_smooth,
            mode='lines+markers',
            name=f'With {total_panels} Panels',
            line=dict(color='#3498db', width=4, smoothing=0.5),
            marker=dict(size=4, color='#3498db', symbol='circle', opacity=0.7),
            hovertemplate="<b>With Treatment</b><br>Frequency: %{x} Hz<br>RT60: %{y:.2f}s<br><i>Professional broadcast quality</i><extra></extra>"
        ))
        
        # Target curve (ideal goal) - smooth green curve
        fig.add_trace(go.Scatter(
            x=extended_freqs,
            y=target_smooth,
            mode='lines',
            name='Broadcast Target',
            line=dict(color='#27ae60', width=3, dash='dot', smoothing=0.5),
            hovertemplate="<b>Broadcast Target</b><br>Frequency: %{x} Hz<br>RT60: %{y:.2f}s<br><i>Optimal for speech clarity</i><extra></extra>"
        ))
        
        # Calculate improvement percentage for title
        avg_current = np.mean(current_smooth)
        avg_treated = np.mean(treated_smooth)
        improvement_pct = ((avg_current - avg_treated) / avg_current) * 100
        
        # Transform frequency data with extended range (30Hz to 3kHz)
        def transform_frequency_scale(freq):
            """Transform frequency to evenly spaced positions with 30Hz-3kHz boundaries"""
            # Extended tick frequencies with 30Hz and 3kHz boundaries
            tick_freqs = [30, 60, 90, 120, 180, 250, 360, 540, 770, 1000, 1500, 2000, 3000]
            
            # Handle frequencies outside our range
            if freq <= tick_freqs[0]:
                return 0.0
            if freq >= tick_freqs[-1]:
                return float(len(tick_freqs) - 1)
            
            # Find the two adjacent tick frequencies
            for i in range(len(tick_freqs) - 1):
                if tick_freqs[i] <= freq <= tick_freqs[i + 1]:
                    # Linear interpolation between the two evenly spaced positions
                    freq_ratio = (freq - tick_freqs[i]) / (tick_freqs[i + 1] - tick_freqs[i])
                    return float(i) + freq_ratio
            
            return 0.0  # Fallback
        
        # Transform the frequency data for all traces
        transformed_freqs = [transform_frequency_scale(f) for f in extended_freqs]
        
        # Update all traces to use transformed frequencies
        fig.data[0].x = transformed_freqs + transformed_freqs[::-1]  # Target zone
        fig.data[1].x = transformed_freqs  # Current RT60
        fig.data[2].x = transformed_freqs  # Treated RT60
        fig.data[3].x = transformed_freqs  # Target curve
        
        # Set up tick configuration with 30Hz-3kHz range
        tick_freqs = [30, 60, 90, 120, 180, 250, 360, 540, 770, 1000, 1500, 2000, 3000]
        tick_texts = ["30Hz", "60Hz", "90Hz", "120Hz", "180Hz", "250Hz", "360Hz", "540Hz", "770Hz", "1kHz", "1.5kHz", "2kHz", "3kHz"]
        tick_positions = list(range(len(tick_freqs)))  # 0, 1, 2, ... 12
        
        fig.update_layout(
            title="",  # Empty string instead of None to avoid "undefined"
            xaxis=dict(
                title="Frequency (Hz)",
                type="linear",  # Linear scale with pre-transformed data
                range=[0, len(tick_freqs) - 1],  # 0 to 14
                tickmode="array",
                tickvals=tick_positions,
                ticktext=tick_texts,
                gridcolor="rgba(128,128,128,0.2)",
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                title="RT60 (seconds)",
                gridcolor="rgba(128,128,128,0.2)",
                showgrid=True,
                zeroline=False,
                range=[0.2, 1.1],  # Maximized range for broadcast studio RT60 values
                dtick=0.1  # Show ticks every 0.1 seconds
            ),
            plot_bgcolor="rgba(248,249,250,0.8)",
            paper_bgcolor="white",
            height=650,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(128,128,128,0.3)",
                borderwidth=1
            ),
            margin=dict(t=20, b=60, l=60, r=60),
            hovermode='x unified'
        )
        
        # Add subtle styling touches
        fig.update_traces(
            hoverinfo="text",
        )
        
        return fig
    
    def create_treatment_effectiveness_chart(self, panel_counts, drape_removal):
        """Create treatment effectiveness visualization"""
        
        new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
        
        # Calculate improvements
        improvements = {}
        for freq in new_rt60:
            current = self.current_conditions["rt60_by_freq"][freq]
            predicted = new_rt60[freq]
            improvement_pct = ((current - predicted) / current) * 100
            improvements[freq] = max(0, improvement_pct)  # No negative improvements
        
        # Create effectiveness chart
        fig = go.Figure()
        
        frequencies = list(improvements.keys())
        improvement_values = list(improvements.values())
        
        # Color code by effectiveness
        colors = ['#27ae60' if imp > 30 else '#f39c12' if imp > 15 else '#e74c3c' for imp in improvement_values]
        
        fig.add_trace(go.Bar(
            x=frequencies,
            y=improvement_values,
            marker_color=colors,
            name='RT60 Improvement',
            hovertemplate="<b>Frequency: %{x} Hz</b><br>Improvement: %{y:.1f}%<extra></extra>"
        ))
        
        # Add effectiveness thresholds
        fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Excellent (>30%)")
        fig.add_hline(y=15, line_dash="dash", line_color="orange", annotation_text="Good (>15%)")
        
        fig.update_layout(
            title="Treatment Effectiveness by Frequency",
            xaxis_title="Frequency (Hz)",
            yaxis_title="RT60 Improvement (%)",
            height=400
        )
        
        return fig
    
    def create_cost_benefit_analysis(self, max_panels=50):
        """Create cost vs benefit analysis"""
        
        panel_counts = range(1, max_panels + 1)
        costs_2in = []
        costs_3in = []
        costs_5in = []
        benefits_2in = []
        benefits_3in = []
        benefits_5in = []
        
        for count in panel_counts:
            # Costs
            cost_2 = count * self.panel_specs["2_inch"]["cost"]
            cost_3 = count * self.panel_specs["3_inch"]["cost"]
            cost_5 = count * self.panel_specs["5_5_inch"]["cost"]
            costs_2in.append(cost_2)
            costs_3in.append(cost_3)
            costs_5in.append(cost_5)
            
            # Benefits (average RT60 improvement)
            rt60_2 = self.calculate_rt60_with_panels({"2_inch": count, "3_inch": 0, "5_5_inch": 0}, True)
            rt60_3 = self.calculate_rt60_with_panels({"2_inch": 0, "3_inch": count, "5_5_inch": 0}, True)
            rt60_5 = self.calculate_rt60_with_panels({"2_inch": 0, "3_inch": 0, "5_5_inch": count}, True)
            
            current_avg = np.mean(list(self.current_conditions["rt60_by_freq"].values()))
            benefit_2 = ((current_avg - np.mean(list(rt60_2.values()))) / current_avg) * 100
            benefit_3 = ((current_avg - np.mean(list(rt60_3.values()))) / current_avg) * 100
            benefit_5 = ((current_avg - np.mean(list(rt60_5.values()))) / current_avg) * 100
            
            benefits_2in.append(max(0, benefit_2))
            benefits_3in.append(max(0, benefit_3))
            benefits_5in.append(max(0, benefit_5))
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Cost vs Panel Count', 'Benefit vs Cost'),
            specs=[[{"secondary_y": False}, {"secondary_y": True}]]
        )
        
        # Cost chart
        fig.add_trace(
            go.Scatter(x=list(panel_counts), y=costs_2in, name='2" Panels', line=dict(color='green')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=list(panel_counts), y=costs_3in, name='3" Panels', line=dict(color='blue')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=list(panel_counts), y=costs_5in, name='5.5" Panels', line=dict(color='red')),
            row=1, col=1
        )
        
        # Budget line
        fig.add_hline(y=1200, line_dash="dash", line_color="gray", annotation_text="Budget ($1,200)", row=1, col=1)
        
        # Benefit vs cost
        fig.add_trace(
            go.Scatter(x=costs_2in, y=benefits_2in, name='2" Efficiency', mode='markers+lines', marker=dict(color='green')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=costs_3in, y=benefits_3in, name='3" Efficiency', mode='markers+lines', marker=dict(color='blue')),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=costs_5in, y=benefits_5in, name='5.5" Efficiency', mode='markers+lines', marker=dict(color='red')),
            row=1, col=2
        )
        
        fig.update_xaxes(title_text="Panel Count", row=1, col=1)
        fig.update_yaxes(title_text="Cost ($)", row=1, col=1)
        fig.update_xaxes(title_text="Cost ($)", row=1, col=2)
        fig.update_yaxes(title_text="RT60 Improvement (%)", row=1, col=2)
        
        fig.update_layout(
            title="Cost-Benefit Analysis",
            height=500
        )
        
        return fig
    
    def create_position_improvement_heatmap(self, panel_counts, drape_removal):
        """Create position-specific improvement predictions"""
        
        # Calculate overall RT60 improvement
        new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
        current_avg_rt60 = np.mean(list(self.current_conditions["rt60_by_freq"].values()))
        new_avg_rt60 = np.mean(list(new_rt60.values()))
        rt60_improvement = (current_avg_rt60 - new_avg_rt60) / current_avg_rt60
        
        # Estimate position-specific improvements
        position_improvements = {}
        for position, current_sti in self.current_conditions["sti_by_position"].items():
            if "Reference" not in position:
                # Base improvement from RT60 reduction
                base_improvement = rt60_improvement * 0.5  # 50% of RT60 improvement translates to STI
                
                # Position-specific factors
                if "Corner" in position:
                    # Corners benefit more from treatment
                    position_factor = 1.3
                elif "Talent" in position:
                    # Key position gets priority benefit
                    position_factor = 1.2
                else:
                    position_factor = 1.0
                
                # Calculate new STI
                sti_improvement = base_improvement * position_factor
                new_sti = min(0.95, current_sti + sti_improvement)
                improvement_pct = ((new_sti - current_sti) / current_sti) * 100
                
                position_improvements[position] = {
                    'current': current_sti,
                    'predicted': new_sti,
                    'improvement_pct': improvement_pct
                }
        
        # Create heatmap data
        positions = list(position_improvements.keys())
        metrics = ['Current STI', 'Predicted STI', 'Improvement %']
        
        heatmap_data = []
        for position in positions:
            row = [
                position_improvements[position]['current'],
                position_improvements[position]['predicted'],
                position_improvements[position]['improvement_pct']
            ]
            heatmap_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=metrics,
            y=positions,
            colorscale='RdYlGn',
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.2f}<extra></extra>",
            text=[[f"{val:.2f}" for val in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Position-Specific STI Improvement Predictions",
            height=400
        )
        
        return fig
    
    def render_treatment_simulator(self, space="Studio 8"):
        """Main rendering function for treatment simulator"""
        
        # Show space-specific info
        if space == "The Hub":
            st.info("**Interactive Panel Planning:** Build your acoustic treatment package for The Hub. Note: Currently showing Studio 8 data as baseline - Hub-specific calculations coming soon.")
        else:
            st.info("**Interactive Panel Planning:** Build your acoustic treatment package by selecting quantities of different panel thicknesses. See real-time acoustic impact and cost calculations.")
        
        # Load space-specific data
        self._load_space_parameters(space)
        self.drape_data = self._load_drape_data(space)
        
        # Control panel
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Panel Planning")
            
            # Drape removal consideration - only for Studio 8
            if space == "Studio 8":
                st.markdown("**Drape Impact Analysis**")
                drape_removal = st.checkbox(
                    "Account for Lighting Grid Drape Removal",
                    value=True
                )
                
                if drape_removal:
                    # Calculate equivalent panels for integrated message
                    equivalent_panels = self._calculate_equivalent_panels()
                    st.warning(f"**Drape Removal Impact:** Removing the velvet drape will increase reverberation, especially in mid-frequencies. "
                              f"Your panel selection compensates for this.\n\n"
                              f"**Equivalent compensation:** 4 x 3\" panels OR 3 x 5.5\" panels needed to offset drape removal.")
                else:
                    st.info("**Drape Retained:** Calculations assume the lighting grid drape remains in place.")
                
                st.markdown("---")
            else:
                # For The Hub, no drape to remove
                drape_removal = False
            
            # Initialize session state for panel counts - space-specific defaults
            if space == "Studio 8":
                # Studio 8 defaults: 25 total panels (4 + 8 + 13 = 25)
                if 'panel_2_inch' not in st.session_state:
                    st.session_state.panel_2_inch = 4
                if 'panel_3_inch' not in st.session_state:
                    st.session_state.panel_3_inch = 8
                if 'panel_5_5_inch' not in st.session_state:
                    st.session_state.panel_5_5_inch = 13
            else:
                # The Hub defaults: 10 total panels (2 + 3 + 5 = 10)
                if 'panel_2_inch' not in st.session_state:
                    st.session_state.panel_2_inch = 2
                if 'panel_3_inch' not in st.session_state:
                    st.session_state.panel_3_inch = 3
                if 'panel_5_5_inch' not in st.session_state:
                    st.session_state.panel_5_5_inch = 5
            
            # Shopping cart style selectors - horizontal layout
            st.markdown("**Panels (Mineral Wool, Framing, Hardware, Fabric)**")
            col_5, col_3, col_2 = st.columns(3)
            
            with col_5:
                st.markdown("**5.5\" @ $30 ea.**")
                panel_5_5_count = st.number_input(
                    "Qty:",
                    min_value=0,
                    max_value=50,
                    value=st.session_state.panel_5_5_inch,
                    step=1,
                    key="panel_5_5_input",
                    help="Excellent broadband absorption, especially low frequencies (125Hz+)"
                )
                st.session_state.panel_5_5_inch = panel_5_5_count
            
            with col_3:
                st.markdown("**3\" @ $25 ea.**")
                panel_3_count = st.number_input(
                    "Qty:",
                    min_value=0,
                    max_value=50,
                    value=st.session_state.panel_3_inch,
                    step=1,
                    key="panel_3_input",
                    help="Good for mid-to-high frequency absorption (500Hz+)"
                )
                st.session_state.panel_3_inch = panel_3_count
            
            with col_2:
                st.markdown("**2\" @ $20 ea.**")
                panel_2_count = st.number_input(
                    "Qty:",
                    min_value=0,
                    max_value=50,
                    value=st.session_state.panel_2_inch,
                    step=1,
                    key="panel_2_input",
                    help="Budget option for high-frequency absorption (1kHz+)"
                )
                st.session_state.panel_2_inch = panel_2_count
            
            # Create panel counts dictionary
            panel_counts = {
                "2_inch": panel_2_count,
                "3_inch": panel_3_count,
                "5_5_inch": panel_5_5_count
            }
            
            # Calculate totals
            total_panels = panel_2_count + panel_3_count + panel_5_5_count
            cost_2_inch = panel_2_count * self.panel_specs["2_inch"]["cost"]
            cost_3_inch = panel_3_count * self.panel_specs["3_inch"]["cost"]
            cost_5_5_inch = panel_5_5_count * self.panel_specs["5_5_inch"]["cost"]
            total_cost = cost_2_inch + cost_3_inch + cost_5_5_inch
            budget_remaining = 1200 - total_cost
            
            # Display cart contents
            st.markdown("---")
            st.subheader("Cart Summary")
            if total_panels > 0:
                if panel_5_5_count > 0:
                    st.write(f"• {panel_5_5_count}x 5.5\" panels: ${cost_5_5_inch}")
                if panel_3_count > 0:
                    st.write(f"• {panel_3_count}x 3\" panels: ${cost_3_inch}")
                if panel_2_count > 0:
                    st.write(f"• {panel_2_count}x 2\" panels: ${cost_2_inch}")
                
                st.markdown(f"**Total: {total_panels} panels for ${total_cost} before HST**")
                
                if budget_remaining >= 0:
                    st.success(f"${budget_remaining} remaining in budget")
                else:
                    st.error(f"${abs(budget_remaining)} over budget")
                
                # Add cost efficiency metrics here (moved from detailed breakdown)
                # Calculate additional costs for efficiency metrics
                labor_cost = min(300, total_panels * 8)  # $8 per panel, max $300
                hardware_cost = total_panels * 3  # $3 per panel for mounting hardware
                fabric_cost = total_panels * 5  # $5 per panel for acoustic fabric
                total_with_extras = total_cost + labor_cost + hardware_cost + fabric_cost
                
                # Calculate RT60 improvement for efficiency
                new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
                avg_rt60_improvement = ((np.mean(list(self.current_conditions["rt60_by_freq"].values())) - 
                                        np.mean(list(new_rt60.values()))) / 
                                       np.mean(list(self.current_conditions["rt60_by_freq"].values()))) * 100
                
                st.markdown("---")
                st.markdown(f"**Total Project: ${total_with_extras}**")
                
                # Budget analysis
                if total_with_extras <= 1200:
                    st.success(f"✅ Within ${1200} budget\n\nRemaining: ${1200 - total_with_extras}")
                elif total_cost <= 1200:
                    st.warning(f"⚠️ Panels fit budget, but total project exceeds by ${total_with_extras - 1200}")
                else:
                    st.error(f"❌ Over budget by ${total_with_extras - 1200}")
                
                st.markdown("**Cost Efficiency:**")
                cost_per_panel = total_with_extras / total_panels if total_panels > 0 else 0
                rt60_improvement_per_dollar = (avg_rt60_improvement / total_with_extras * 100) if total_with_extras > 0 else 0
                
                st.write(f"• ${cost_per_panel:.0f} per panel (all-in)")
                st.write(f"• {rt60_improvement_per_dollar:.2f}% RT60 improvement per $100")
            else:
                st.write("*Cart is empty - add some panels above*")
        
        with col2:
            # Visualization tabs (Position Impact hidden)
            tab1, tab2, tab3 = st.tabs(["Before/After", "Effectiveness", "Cost-Benefit"])
            
            with tab1:
                fig_comparison = self.create_before_after_comparison(panel_counts, drape_removal)
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            with tab2:
                fig_effectiveness = self.create_treatment_effectiveness_chart(panel_counts, drape_removal)
                st.plotly_chart(fig_effectiveness, use_container_width=True)
            
            with tab3:
                fig_cost_benefit = self.create_cost_benefit_analysis()
                st.plotly_chart(fig_cost_benefit, use_container_width=True)
        
        # Treatment Summary - right underneath the charts
        if total_panels > 0:
            st.subheader("Treatment Summary")
            
            new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
            avg_rt60_improvement = ((np.mean(list(self.current_conditions["rt60_by_freq"].values())) - 
                                    np.mean(list(new_rt60.values()))) / 
                                   np.mean(list(self.current_conditions["rt60_by_freq"].values()))) * 100
            
            predicted_sti = self.calculate_sti_improvement(avg_rt60_improvement)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                breakdown_parts = []
                if panel_2_count > 0:
                    breakdown_parts.append(f"{panel_2_count}x 2\"")
                if panel_3_count > 0:
                    breakdown_parts.append(f"{panel_3_count}x 3\"")
                if panel_5_5_count > 0:
                    breakdown_parts.append(f"{panel_5_5_count}x 5.5\"")
                panel_breakdown = " + ".join(breakdown_parts) if breakdown_parts else "None"
                st.metric("Panels", f"{total_panels}", panel_breakdown)
            
            with col2:
                st.metric("Cost", f"${total_cost}", f"${budget_remaining} budget remaining")
            
            with col3:
                current_avg = np.mean(list(self.current_conditions["rt60_by_freq"].values()))
                new_avg = np.mean(list(new_rt60.values()))
                st.metric("Avg RT60", f"{new_avg:.2f}s", f"{((current_avg - new_avg) / current_avg * 100):.1f}% improvement")
            
            with col4:
                st.metric("Predicted STI", f"{predicted_sti:.2f}", f"{((predicted_sti - 0.67) / 0.67 * 100):.1f}% improvement")
            
            # Add spacing between Treatment Summary and detailed sections
            st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Detailed recommendations and cost breakdown (always visible)
        if total_panels > 0:
            detail_col1, detail_col2 = st.columns([2, 1])
            
            with detail_col1:
                st.subheader("Detailed Recommendations")
                new_rt60 = self.calculate_rt60_with_panels(panel_counts, drape_removal)
                avg_rt60_improvement = ((np.mean(list(self.current_conditions["rt60_by_freq"].values())) - 
                                        np.mean(list(new_rt60.values()))) / 
                                       np.mean(list(self.current_conditions["rt60_by_freq"].values()))) * 100
                predicted_sti = self.calculate_sti_improvement(avg_rt60_improvement)
                
                st.write("**Optimal Panel Placement:**")
                
                if total_panels <= 8:
                    st.write("- **Phase 1 (Minimal Treatment):** Basic drape compensation")
                    st.write("  • 4-6 panels: Ceiling-mounted above lighting grid (center area)")
                    st.write("  • 2-4 panels: Corner ceiling positions for modal control")
                    st.write("  • Focus: Compensate for drape removal impact")
                elif total_panels <= 16:
                    st.write("- **Phase 2 (Essential Treatment):** Foundation acoustics")
                    st.write("  • 4 panels: Corner bass traps (straddle-mount, above grid)")
                    st.write("  • 6-8 panels: Center ceiling treatment (primary reflection zone)")
                    st.write("  • 4 panels: North/South/East/West midpoint ceiling positions")
                    st.write("  • Focus: Modal control + primary reflection management")
                elif total_panels <= 24:
                    st.write("- **Phase 3 (Comprehensive Treatment):** Professional standard")
                    st.write("  • 4 panels: Corner bass traps (5.5\" recommended)")
                    st.write("  • 8 panels: Ceiling treatment grid (above lighting)")
                    st.write("  • 6 panels: First reflection points (side walls, mid-height)")
                    st.write("  • 4-6 panels: North wall (off-camera positions)")
                    st.write("  • Focus: Broadcast-quality speech intelligibility")
                elif total_panels <= 35:
                    st.write("- **Phase 4 (Enhanced Treatment):** Premium acoustics")
                    st.write("  • 6 panels: Enhanced corner bass traps (double thickness)")
                    st.write("  • 10-12 panels: Complete ceiling grid coverage")
                    st.write("  • 8 panels: Wall first reflection points")
                    st.write("  • 6 panels: Secondary reflection control (rear wall)")
                    st.write("  • 4 panels: Fine-tuning positions")
                    st.write("  • Focus: Exceptional clarity across all positions")
                else:
                    st.write("- **Phase 5 (Maximum Treatment):** Studio reference standard")
                    st.write("  • 8 panels: Triple corner bass trap system")
                    st.write("  • 15+ panels: Complete lighting absorption field")
                    st.write("  • 10+ panels: Comprehensive wall treatment")
                    st.write("  • Remaining panels: Custom problem area targeting")
                    st.write("  • Focus: Reference-grade acoustic environment")
                
                # Panel type recommendations
                max_count = max(panel_2_count, panel_3_count, panel_5_5_count)
                if panel_5_5_count == max_count and panel_5_5_count > 0:
                    st.write("\n**Panel Planning:** Excellent choice prioritizing 5.5\" panels for broadband absorption.")
                elif panel_3_count == max_count and panel_3_count > 0:
                    st.write("\n**Panel Planning:** Good mid-high frequency focus with 3\" panels. Consider more 5.5\" for low-frequency control.")
                elif panel_2_count == max_count and panel_2_count > 0:
                    st.write("\n**Panel Planning:** Budget-conscious approach with 2\" panels. Great for high frequencies, but consider thicker panels for bass control.")
                else:
                    st.write("\n**Panel Planning:** Balanced mix of panel thicknesses for comprehensive frequency coverage.")
                
                # Drape-specific guidance
                if drape_removal:
                    st.write("\n**Drape Impact:** Your panel count compensates for drape removal. Priority: ceiling panels above grid area.")
                else:
                    st.write("\n**Drape Retained:** Existing drape provides some mid-frequency absorption. Focus panels on corners and walls.")
                
                st.write(f"\n**Expected Results:**")
                st.write(f"- RT60 reduction: {avg_rt60_improvement:.1f}% average")
                st.write(f"- STI improvement: {((predicted_sti - 0.67) / 0.67 * 100):.1f}%")
                st.write(f"- Speech clarity: {'Excellent' if predicted_sti > 0.75 else 'Good' if predicted_sti > 0.6 else 'Fair'}")
                st.write(f"- Total coverage: {(total_panels * 8) / self.room_surface_area * 100:.1f}% of room surface area")
            
            with detail_col2:
                st.subheader("Panel Costs")
                
                # Panel costs breakdown (no subheading)
                if panel_5_5_count > 0:
                    st.write(f"• {panel_5_5_count}x 5.5\" @ $30 ea: **${cost_5_5_inch}**")
                if panel_3_count > 0:
                    st.write(f"• {panel_3_count}x 3\" @ $25 ea: **${cost_3_inch}**")
                if panel_2_count > 0:
                    st.write(f"• {panel_2_count}x 2\" @ $20 ea: **${cost_2_inch}**")
                
                st.markdown("---")
                st.markdown(f"**Subtotal: ${total_cost}**")
                
                # Additional costs
                st.markdown("**Additional Costs:**")
                labor_cost = min(300, total_panels * 8)  # $8 per panel, max $300
                hardware_cost = total_panels * 3  # $3 per panel for mounting hardware
                fabric_cost = total_panels * 5  # $5 per panel for acoustic fabric
                
                st.write(f"• Installation labor: **${labor_cost}**")
                st.write(f"• Mounting hardware: **${hardware_cost}**")
                st.write(f"• Acoustic fabric: **${fabric_cost}**")
                
                # Tax note
                st.markdown("---")
                st.caption("*All prices in CAD before HST (13%)")
                hst_amount = (total_cost + labor_cost + hardware_cost + fabric_cost) * 0.13
                total_with_tax = (total_cost + labor_cost + hardware_cost + fabric_cost) + hst_amount
                st.caption(f"Total with HST: ${total_with_tax:.0f}")

if __name__ == "__main__":
    simulator = TreatmentSimulator()
    simulator.render_treatment_simulator()