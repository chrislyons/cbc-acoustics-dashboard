#!/usr/bin/env python3
"""
Advanced Frequency Response Explorer
Interactive analysis of acoustic measurements with real-time filtering
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import re

class FrequencyResponseExplorer:
    def __init__(self):
        self.base_path = Path('/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard')
        self.smaart_data = None
        self.measurement_positions = {}
        self.position_column = None
        # Force clear any cached data
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        
    def get_position_column(self):
        """Get the position column name from the data"""
        if self.smaart_data is None:
            return None
        for col in ['position', 'Position', 'pos', 'location']:
            if col in self.smaart_data.columns:
                return col
        return None
        
    def load_smaart_data(self, space="Studio 8"):
        """Load and parse Smaart measurement data"""
        try:
            # Use the Complete Frequency Response files 
            if space == "Studio 8":
                file_candidates = [
                    "250728-Studio8-Complete_Frequency_Response.csv"
                ]
            else:  # The Hub
                file_candidates = [
                    "250731-TheHub-Complete_Frequency_Response.csv"
                ]
            
            # Try multiple possible paths for the data files
            for filename in file_candidates:
                possible_paths = [
                    self.base_path / f"data/generated/{filename}",
                    Path(f"data/generated/{filename}"),
                    Path(f"./data/generated/{filename}"),
                    Path(f"/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard/data/generated/{filename}")
                ]
                
                for detailed_freq_file in possible_paths:
                    if detailed_freq_file.exists():
                        self.smaart_data = pd.read_csv(detailed_freq_file)
                        
                        unique_positions = self.smaart_data['position'].unique()
                        return True
            
            # File not found in any location - NO SYNTHETIC DATA
            st.error(f"Frequency Response data file not found. Real measurement data required.")
            return False
            
        except Exception as e:
            st.error(f"Error loading Smaart data: {e}")
            return False
    
    def create_synthetic_data(self):
        """Create realistic synthetic acoustic data based on analysis"""
        
        # Frequency range from 20 Hz to 20 kHz
        frequencies = np.logspace(1.3, 4.3, 100)
        
        # Studio 8 measurement positions with realistic degradation patterns
        positions_data = {
            'Host A (Reference)': {
                'STI': 0.95,
                'RT60': 0.32,
                'degradation': 0.0,
                'color': '#27ae60'
            },
            'Host C (Talent)': {
                'STI': 0.67,
                'RT60': 0.78,
                'degradation': 25.3,
                'color': '#e74c3c'
            },
            'Mid Room': {
                'STI': 0.71,
                'RT60': 0.72,
                'degradation': 21.8,
                'color': '#f39c12'
            },
            'NE Corner': {
                'STI': 0.58,
                'RT60': 0.92,
                'degradation': 35.7,
                'color': '#8e44ad'
            },
            'SE Corner': {
                'STI': 0.62,
                'RT60': 0.85,
                'degradation': 30.4,
                'color': '#e67e22'
            },
            'Ceiling': {
                'STI': 0.64,
                'RT60': 0.88,
                'degradation': 32.1,
                'color': '#3498db'
            }
        }
        
        # Generate frequency response data
        data_rows = []
        
        for position, metrics in positions_data.items():
            for freq in frequencies:
                # Create realistic frequency response with modal resonances
                base_response = self._generate_room_response(freq, metrics['RT60'])
                
                # Add position-specific variations
                position_factor = 1.0 + (metrics['degradation'] / 100) * self._position_modifier(freq, position)
                
                response = base_response * position_factor
                
                data_rows.append({
                    'position': position,  # Use lowercase to match CSV
                    'Frequency_Hz': freq,
                    'Magnitude_dB': 20 * np.log10(abs(response)),
                    'Phase_deg': np.angle(response) * 180 / np.pi,
                    'STI': metrics['STI'],
                    'RT60': metrics['RT60'],
                    'STI_Degradation_%': metrics['degradation'],
                    'Color': metrics['color']
                })
        
        self.smaart_data = pd.DataFrame(data_rows)
        
        # Store position metadata
        self.measurement_positions = positions_data
    
    def _generate_room_response(self, frequency, rt60):
        """Generate realistic room frequency response"""
        
        # Modal resonances for Studio 8 (from analysis)
        modal_frequencies = [23.1, 29.1, 37.8, 50.0, 63.0, 74.3, 108.3, 152.8, 206.8, 258.8, 317.9, 448.4, 561.2, 679.0]
        
        response = 1.0 + 0j
        
        # Add modal resonances
        for modal_freq in modal_frequencies:
            if frequency < 1000:  # Low frequency focus
                q_factor = 50 / rt60  # Higher RT60 = lower Q
                modal_response = 1 / (1 + 1j * q_factor * (frequency / modal_freq - modal_freq / frequency))
                response += 0.3 * modal_response
        
        # Add high frequency roll-off
        if frequency > 2000:
            rolloff = np.exp(-(frequency - 2000) / 8000)
            response *= rolloff
        
        # Add room absorption effects
        absorption_factor = 1 / (1 + rt60 * frequency / 1000)
        response *= absorption_factor
        
        return response
    
    def _position_modifier(self, frequency, position):
        """Position-specific frequency response modifiers"""
        
        if 'Corner' in position:
            # Corners have more bass buildup
            if frequency < 200:
                return 0.5 * np.sin(frequency / 30)
            else:
                return 0.1
        
        elif 'Reference' in position:
            # Reference position is close to source
            return -0.8  # Less room effect
        
        elif 'Talent' in position:
            # Talent position has significant room interaction
            return 0.3 * np.sin(frequency / 100)
        
        elif 'Ceiling' in position:
            # Ceiling position has different modal patterns
            return 0.2 * np.cos(frequency / 80)
        
        else:
            return 0.1 * np.sin(frequency / 150)
    
    def transform_frequency_scale(self, freq):
        """Transform frequency to evenly spaced positions matching tick arrangement"""
        import math
        
        # Define our evenly spaced reference frequencies (30Hz to 3000Hz)
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
    
    def inverse_transform_frequency_scale(self, transformed_val):
        """Convert transformed scale back to frequency"""
        import numpy as np
        
        low_section_width = 0.5 * np.log10(100 / 20)
        mid_section_width = np.log10(2000 / 100) 
        
        if transformed_val <= low_section_width:
            # Low section: 20Hz-100Hz
            return 20 * (10 ** (transformed_val / 0.5))
        elif transformed_val <= low_section_width + mid_section_width:
            # Mid section: 100Hz-2kHz
            mid_val = transformed_val - low_section_width
            return 100 * (10 ** mid_val)
        else:
            # High section: >2kHz
            high_val = transformed_val - low_section_width - mid_section_width
            return 2000 * (10 ** (high_val / 0.5))

    def create_interactive_frequency_plot(self, freq_range=(30, 3000)):
        """Create main interactive frequency response plot
        
        Args:
            freq_range (tuple): Frequency range as (min_freq, max_freq) in Hz
        """
        
        if self.smaart_data is None:
            self.load_smaart_data()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('', ''),
            vertical_spacing=0.15,
            shared_xaxes=True,
            x_title="Frequency (Hz)"
        )
        
        # Get unique positions
        position_col = self.get_position_column()
        if not position_col:
            st.error("No position column found in data")
            return go.Figure()
            
        positions = self.smaart_data[position_col].unique()
        
        for position in positions:
            pos_data = self.smaart_data[self.smaart_data[position_col] == position]
            
            # Filter data by frequency range
            freq_mask = (pos_data['Frequency_Hz'] >= freq_range[0]) & (pos_data['Frequency_Hz'] <= freq_range[1])
            pos_data = pos_data[freq_mask]
            
            # Transform frequency values to custom scale
            transformed_freq = [self.transform_frequency_scale(f) for f in pos_data['Frequency_Hz']]
            
            color = pos_data['Color'].iloc[0] if 'Color' in pos_data.columns else None
            
            # Magnitude plot
            fig.add_trace(
                go.Scatter(
                    x=transformed_freq,
                    y=pos_data['Magnitude_dB'],
                    mode='lines',
                    name=position,
                    line=dict(color=color, width=2, shape='linear'),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                  "Frequency: %{customdata:.0f} Hz<br>" +
                                  "Magnitude: %{y:.1f} dB<br>" +
                                  "<extra></extra>",
                    customdata=pos_data['Frequency_Hz'],
                    showlegend=True
                ),
                row=1, col=1
            )
            
            # Phase plot
            fig.add_trace(
                go.Scatter(
                    x=transformed_freq,
                    y=pos_data['Phase_deg'],
                    mode='lines',
                    name=f"{position} (Phase)",
                    line=dict(color=color, width=2, dash='dot', shape='linear'),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                  "Frequency: %{customdata:.0f} Hz<br>" +
                                  "Phase: %{y:.1f}°<br>" +
                                  "<extra></extra>",
                    customdata=pos_data['Frequency_Hz'],
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Update layout with custom frequency axis scaling
        import math
        
        # Transform frequency range to evenly spaced scale (0 to 12 for 13 ticks)
        transformed_min = self.transform_frequency_scale(max(freq_range[0], 30))
        transformed_max = self.transform_frequency_scale(min(freq_range[1], 3000))
        
        # Generate evenly spaced positions but use preferred standard frequencies (30Hz to 3kHz)
        all_tick_freqs = [30, 60, 90, 120, 180, 250, 360, 540, 770, 1000, 1500, 2000, 3000]
        all_tick_text = ["30Hz", "60Hz", "90Hz", "120Hz", "180Hz", "250Hz", "360Hz", "540Hz", "770Hz", "1kHz", "1.5kHz", "2kHz", "3kHz"]
        
        # Filter and evenly space tick positions
        filtered_ticks = [(freq, text) for freq, text in zip(all_tick_freqs, all_tick_text) 
                         if freq_range[0] <= freq <= freq_range[1]]
        
        if filtered_ticks:
            tick_freqs, tick_texts = zip(*filtered_ticks)
            # Use the transform function to get correct positions
            transformed_tick_positions = [self.transform_frequency_scale(f) for f in tick_freqs]
        else:
            tick_freqs = [freq_range[0]]
            tick_texts = [f"{freq_range[0]}Hz"]  
            transformed_tick_positions = [transformed_min]
        
        x_axis_config = dict(
            type="linear",  # Use linear since we're pre-transforming the data
            range=[transformed_min, transformed_max],
            tickmode="array",
            tickvals=transformed_tick_positions,
            ticktext=list(tick_texts),
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray"
        )
        
        # Apply to both magnitude and phase response charts
        fig.update_xaxes(**x_axis_config, row=1, col=1)  # Magnitude response 
        fig.update_xaxes(**x_axis_config, row=2, col=1)  # Phase response
        
        # Show tick labels on both charts for better readability
        fig.update_xaxes(showticklabels=True, row=1, col=1)
        fig.update_xaxes(showticklabels=True, row=2, col=1)
        
        fig.update_yaxes(title_text="Magnitude (dB)", row=1, col=1)
        fig.update_yaxes(title_text="Phase (degrees)", row=2, col=1)
        
        fig.update_layout(
            title="Frequency Response Analysis",
            height=800,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=1.02,
                groupclick="toggleitem",  # Enable individual trace toggling
                itemclick="toggle",       # Single click toggles individual traces
                itemdoubleclick="toggleothers"  # Double click isolates single trace
            )
        )
        
        # Add instruction text for legend interaction
        fig.add_annotation(
            text="<b>Legend:</b> Click to toggle • Double-click to solo",
            xref="paper", yref="paper",
            x=1.02, y=0.02,
            xanchor="left", yanchor="bottom",
            font=dict(size=10, color="gray"),
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        )
        
        return fig
    
    def create_magnitude_response_plot(self, freq_range=(30, 3000)):
        """Create magnitude-only frequency response plot"""
        
        if self.smaart_data is None:
            self.load_smaart_data()
        
        fig = go.Figure()
        
        # Get unique positions
        position_col = self.get_position_column()
        if not position_col:
            st.error("No position column found in data")
            return go.Figure()
            
        positions = self.smaart_data[position_col].unique()
        
        for position in positions:
            pos_data = self.smaart_data[self.smaart_data[position_col] == position]
            
            # Filter data by frequency range
            freq_mask = (pos_data['Frequency_Hz'] >= freq_range[0]) & (pos_data['Frequency_Hz'] <= freq_range[1])
            pos_data = pos_data[freq_mask]
            
            # Transform frequency values to custom scale
            transformed_freq = [self.transform_frequency_scale(f) for f in pos_data['Frequency_Hz']]
            
            color = pos_data['Color'].iloc[0] if 'Color' in pos_data.columns else None
            
            # Magnitude plot only
            fig.add_trace(
                go.Scatter(
                    x=transformed_freq,
                    y=pos_data['Magnitude_dB'],
                    mode='lines',
                    name=position,
                    line=dict(color=color, width=2, shape='linear'),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                  "Frequency: %{customdata:.0f} Hz<br>" +
                                  "Magnitude: %{y:.1f} dB<br>" +
                                  "<extra></extra>",
                    customdata=pos_data['Frequency_Hz'],
                    showlegend=True
                )
            )
        
        # Update layout for magnitude only
        transformed_min = self.transform_frequency_scale(max(freq_range[0], 30))
        transformed_max = self.transform_frequency_scale(min(freq_range[1], 3000))
        
        all_tick_freqs = [30, 60, 90, 120, 180, 250, 360, 540, 770, 1000, 1500, 2000, 3000]
        all_tick_text = ["30Hz", "60Hz", "90Hz", "120Hz", "180Hz", "250Hz", "360Hz", "540Hz", "770Hz", "1kHz", "1.5kHz", "2kHz", "3kHz"]
        
        filtered_ticks = [(freq, text) for freq, text in zip(all_tick_freqs, all_tick_text) 
                         if freq_range[0] <= freq <= freq_range[1]]
        
        if filtered_ticks:
            tick_freqs, tick_texts = zip(*filtered_ticks)
            transformed_tick_positions = [self.transform_frequency_scale(f) for f in tick_freqs]
        else:
            tick_freqs = [freq_range[0]]
            tick_texts = [f"{freq_range[0]}Hz"]  
            transformed_tick_positions = [transformed_min]
        
        fig.update_layout(
            title="Magnitude Response Analysis",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Magnitude (dB)",
            height=800,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=1.02,
                groupclick="toggleitem",
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            xaxis=dict(
                type="linear",
                range=[transformed_min, transformed_max],
                tickmode="array",
                tickvals=transformed_tick_positions,
                ticktext=list(tick_texts),
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray"
            )
        )
        
        return fig
    
    def create_phase_response_plot(self, freq_range=(30, 3000)):
        """Create phase-only frequency response plot"""
        
        if self.smaart_data is None:
            self.load_smaart_data()
        
        fig = go.Figure()
        
        # Get unique positions
        position_col = self.get_position_column()
        if not position_col:
            st.error("No position column found in data")
            return go.Figure()
            
        positions = self.smaart_data[position_col].unique()
        
        for position in positions:
            pos_data = self.smaart_data[self.smaart_data[position_col] == position]
            
            # Filter data by frequency range
            freq_mask = (pos_data['Frequency_Hz'] >= freq_range[0]) & (pos_data['Frequency_Hz'] <= freq_range[1])
            pos_data = pos_data[freq_mask]
            
            # Transform frequency values to custom scale
            transformed_freq = [self.transform_frequency_scale(f) for f in pos_data['Frequency_Hz']]
            
            color = pos_data['Color'].iloc[0] if 'Color' in pos_data.columns else None
            
            # Phase plot only
            fig.add_trace(
                go.Scatter(
                    x=transformed_freq,
                    y=pos_data['Phase_deg'],
                    mode='lines',
                    name=position,
                    line=dict(color=color, width=2, shape='linear'),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                  "Frequency: %{customdata:.0f} Hz<br>" +
                                  "Phase: %{y:.1f}°<br>" +
                                  "<extra></extra>",
                    customdata=pos_data['Frequency_Hz'],
                    showlegend=True
                )
            )
        
        # Update layout for phase only
        transformed_min = self.transform_frequency_scale(max(freq_range[0], 30))
        transformed_max = self.transform_frequency_scale(min(freq_range[1], 3000))
        
        all_tick_freqs = [30, 60, 90, 120, 180, 250, 360, 540, 770, 1000, 1500, 2000, 3000]
        all_tick_text = ["30Hz", "60Hz", "90Hz", "120Hz", "180Hz", "250Hz", "360Hz", "540Hz", "770Hz", "1kHz", "1.5kHz", "2kHz", "3kHz"]
        
        filtered_ticks = [(freq, text) for freq, text in zip(all_tick_freqs, all_tick_text) 
                         if freq_range[0] <= freq <= freq_range[1]]
        
        if filtered_ticks:
            tick_freqs, tick_texts = zip(*filtered_ticks)
            transformed_tick_positions = [self.transform_frequency_scale(f) for f in tick_freqs]
        else:
            tick_freqs = [freq_range[0]]
            tick_texts = [f"{freq_range[0]}Hz"]  
            transformed_tick_positions = [transformed_min]
        
        fig.update_layout(
            title="Phase Response Analysis",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Phase (degrees)",
            height=800,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=1.02,
                groupclick="toggleitem",
                itemclick="toggle",
                itemdoubleclick="toggleothers"
            ),
            xaxis=dict(
                type="linear",
                range=[transformed_min, transformed_max],
                tickmode="array",
                tickvals=transformed_tick_positions,
                ticktext=list(tick_texts),
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray"
            )
        )
        
        return fig
    
    def create_modal_analysis_plot(self, space="Studio 8"):
        """Create modal analysis visualization"""
        
        # Try to load from CSV file first - space-specific
        if space == "Studio 8":
            csv_file = 'data/generated/250728-Studio8-Modal_Stack_Analysis.csv'
        else:  # The Hub
            csv_file = 'data/generated/250728-TheHub-Modal_Stack_Analysis.csv'
        try:
            modal_df = pd.read_csv(csv_file)
            
            # Map CSV columns to expected format
            if 'Primary_Mode_Hz' in modal_df.columns:
                modal_df['Frequency_Hz'] = modal_df['Primary_Mode_Hz']
            
            # Create mode types from Mode_Types column
            if 'Mode_Types' in modal_df.columns:
                modal_df['Mode_Type'] = modal_df['Mode_Types'].fillna('Mixed')
            else:
                modal_df['Mode_Type'] = 'Mixed'
            
            # Create severity based on Treatment_Priority
            if 'Treatment_Priority' in modal_df.columns:
                severity_map = {'Critical': 'High', 'High': 'High', 'Medium': 'Medium', 'Low': 'Low'}
                modal_df['Severity'] = modal_df['Treatment_Priority'].map(severity_map).fillna('Medium')
            else:
                modal_df['Severity'] = 'Medium'
            
            # Create Q_Factor based on Mode_Count (higher mode count = higher Q factor)
            if 'Mode_Count' in modal_df.columns:
                # Scale mode count to Q factor range (higher count = more problematic)
                max_count = modal_df['Mode_Count'].max()
                modal_df['Q_Factor'] = (modal_df['Mode_Count'] / max_count * 40 + 10).round().astype(int)
            else:
                modal_df['Q_Factor'] = 25
                
        except FileNotFoundError:
            # Fallback to hardcoded data if CSV not found - space-specific
            if space == "Studio 8":
                modal_data = {
                    'Frequency_Hz': [23.1, 29.1, 37.8, 50.0, 63.0, 74.3, 108.3, 152.8, 206.8, 258.8, 317.9, 448.4, 561.2, 679.0],
                    'Mode_Type': ['Axial (W)', 'Axial (L)', 'Axial (H)', 'Tangential', 'Axial (W)', 'Axial (L)', 'Tangential', 'Oblique', 'Axial (W)', 'Axial (L)', 'Tangental', 'Oblique', 'Axial (W)', 'Axial (L)'],
                    'Severity': ['High', 'High', 'Medium', 'Medium', 'High', 'Medium', 'Medium', 'Low', 'Medium', 'Medium', 'Low', 'Low', 'Low', 'Low'],
                    'Q_Factor': [45, 38, 28, 35, 42, 32, 25, 18, 22, 28, 15, 12, 10, 8]
                }
            else:  # The Hub - hexagonal space with different modal characteristics
                modal_data = {
                    'Frequency_Hz': [62, 85, 145, 230, 340, 580, 920, 1450, 2300],
                    'Mode_Type': ['Hexagonal', 'Tangential', 'Oblique', 'Mixed', 'Hexagonal', 'Mixed', 'High Order', 'High Order', 'High Order'],
                    'Severity': ['High', 'Medium', 'High', 'Medium', 'High', 'Medium', 'Low', 'Low', 'Low'],
                    'Q_Factor': [35, 28, 40, 25, 38, 22, 15, 12, 8]
                }
            modal_df = pd.DataFrame(modal_data)
        
        # Load frequency response data and calculate average - space-specific
        freq_response_data = None
        try:
            if space == "Studio 8":
                freq_file = 'data/generated/250728-Studio8-Complete_Frequency_Response.csv'
            else:  # The Hub
                freq_file = 'data/generated/250731-TheHub-Complete_Frequency_Response.csv'
            freq_df = pd.read_csv(freq_file)
            
            # Filter to frequency range of interest (30-500Hz) and exclude reference positions
            if space == "Studio 8":
                # Exclude Host A (reference position)
                freq_filtered = freq_df[
                    (freq_df['Frequency_Hz'] >= 30) & 
                    (freq_df['Frequency_Hz'] <= 500) & 
                    (freq_df['position'] != 'Std8-HostA')
                ]
            else:  # The Hub - no specific reference position, use all positions
                freq_filtered = freq_df[
                    (freq_df['Frequency_Hz'] >= 30) & 
                    (freq_df['Frequency_Hz'] <= 500)
                ]
            
            # Calculate average magnitude across non-reference positions
            avg_freq_response = freq_filtered.groupby('Frequency_Hz')['Magnitude_dB'].mean().reset_index()
            freq_response_data = avg_freq_response
            
        except FileNotFoundError:
            freq_response_data = None
        
        # Color mapping for severity
        color_map = {'High': '#e74c3c', 'Medium': '#f39c12', 'Low': '#27ae60'}
        modal_df['Color'] = modal_df['Severity'].map(color_map)
        
        fig = go.Figure()
        
        # Add frequency response line if available
        if freq_response_data is not None:
            # Normalize magnitude to fit Q_Factor scale (scale to 0-50 range)
            min_mag = freq_response_data['Magnitude_dB'].min()
            max_mag = freq_response_data['Magnitude_dB'].max()
            normalized_mag = 50 * (freq_response_data['Magnitude_dB'] - min_mag) / (max_mag - min_mag)
            
            fig.add_trace(
                go.Scatter(
                    x=freq_response_data['Frequency_Hz'],
                    y=normalized_mag,
                    mode='lines',
                    line=dict(color='rgba(128, 128, 128, 0.4)', width=1, dash='solid'),
                    name='Non-Reference Frequency Response Average',
                    showlegend=False,
                    hovertemplate="<b>Non-Reference Frequency Response Average</b><br>" +
                                  "Frequency: %{x:.1f} Hz<br>" +
                                  "Magnitude: %{customdata:.1f} dB<br>" +
                                  "<extra></extra>",
                    customdata=freq_response_data['Magnitude_dB']
                ))
        
        # Add modal frequency markers
        for _, row in modal_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row['Frequency_Hz']],
                    y=[row['Q_Factor']],
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color=row['Color'],
                        symbol='circle',
                        line=dict(width=2, color='white')
                    ),
                    text=[f"{row['Frequency_Hz']:.1f} Hz"],
                    textposition="bottom center",
                    name=f"{row['Mode_Type']} - {row['Severity']}",
                    showlegend=False,
                    hovertemplate=f"<b>{row['Mode_Type']}</b><br>" +
                                  f"Frequency: {row['Frequency_Hz']:.1f} Hz<br>" +
                                  f"Q Factor: {row['Q_Factor']}<br>" +
                                  f"Severity: {row['Severity']}<br>" +
                                  "<extra></extra>"
                ))
        
        # Add frequency bands for treatment focus
        treatment_bands = [
            {'range': [20, 100], 'label': 'Bass Trap Zone', 'color': 'rgba(231, 76, 60, 0.2)'},
            {'range': [100, 300], 'label': 'Modal Control Zone', 'color': 'rgba(243, 156, 18, 0.2)'},
            {'range': [300, 500], 'label': 'Speech Clarity Zone', 'color': 'rgba(52, 152, 219, 0.2)'}
        ]
        
        for band in treatment_bands:
            fig.add_vrect(
                x0=band['range'][0], x1=band['range'][1],
                fillcolor=band['color'],
                opacity=0.3,
                layer="below",
                line_width=0,
                annotation_text=band['label'],
                annotation_position="top left"
            )
        
        fig.update_layout(
            title=f"{space} - Modal Stack Analysis with Avg. Frequency Response",
            xaxis_title="Frequency (Hz)",
            yaxis_title="Q Factor / Normalized Magnitude",
            xaxis=dict(
                type="linear",
                range=[30, 500],
                tickmode="auto"
            ),
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_degradation_heatmap(self):
        """Create STI degradation heatmap from Smaart measurement data"""
        
        # Load STI data from actual Smaart logs
        try:
            smaart_path = Path('data/raw/250715-smaartLogs/Std8')
            
            # File mapping to positions
            file_mapping = {
                'Std8-HostA-128k-Sweep.txt': 'HostA (Reference)',
                'Std8-HostC-128k-Sweep.txt': 'HostC (Talent)',
                'Std8-Ceiling-128k-Sweep.txt': 'Ceiling',
                'Std8-MidRoom-128k-Sweep.txt': 'MidRoom',
                'Std8-NECorner-High-128k-Sweep.txt': 'NECorner-High',
                'Std8-NECorner-Low-128k-Sweep.txt': 'NECorner-Low',
                'Std8-SECorner-128k-Sweep.txt': 'SECorner',
                'Std8-SWCorner-128k-Sweep.txt': 'SWCorner'
            }
            
            # STI frequency bands available in Smaart data
            sti_freq_bands = [125, 250, 500, 1000, 2000, 4000, 8000]
            freq_labels = [f"{f}Hz" if f < 1000 else f"{f/1000:.0f}kHz" for f in sti_freq_bands]
            
            positions = []
            sti_matrix = []
            reference_sti = None
            
            # First pass: get reference STI values from HostA
            ref_filepath = smaart_path / 'Std8-HostA-128k-Sweep.txt'
            if ref_filepath.exists():
                with open(ref_filepath, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.startswith('STI\t'):
                        parts = line.strip().split('\t')
                        if len(parts) >= 8:  # STI + 7 frequency bands
                            reference_sti = [float(parts[i]) for i in range(2, 9)]  # Skip 'STI' and overall value
                            break
            
            if not reference_sti:
                st.error("Could not load reference STI data from HostA")
                return None
            
            # Second pass: get STI for all positions and calculate degradation
            for filename, position_name in file_mapping.items():
                filepath = smaart_path / filename
                if not filepath.exists():
                    continue
                    
                positions.append(position_name)
                
                # Parse Smaart file for STI data
                sti_values = None
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.startswith('STI\t'):
                        parts = line.strip().split('\t')
                        if len(parts) >= 8:  # STI + 7 frequency bands
                            sti_values = [float(parts[i]) for i in range(2, 9)]  # Skip 'STI' and overall value
                            break
                
                if sti_values:
                    # Calculate STI degradation percentage for each frequency band
                    sti_degradation_row = []
                    for i, (sti_val, ref_val) in enumerate(zip(sti_values, reference_sti)):
                        if ref_val > 0:
                            degradation_percent = ((ref_val - sti_val) / ref_val) * 100
                            sti_degradation_row.append(max(0, degradation_percent))  # Don't show negative degradation
                        else:
                            sti_degradation_row.append(0)
                    
                    sti_matrix.append(sti_degradation_row)
                else:
                    # Fallback with zeros if no STI data found
                    sti_matrix.append([0] * len(sti_freq_bands))
            
            if not positions:
                st.error("No Smaart measurement files found")
                return None
            
            # Create heatmap with balanced red onset for broadcast quality emphasis
            fig = go.Figure(data=go.Heatmap(
                z=sti_matrix,
                x=freq_labels,
                y=positions,
                colorscale=[
                    [0.0, '#40C040'],    # GREEN START - No degradation (ideal)
                    [0.05, '#50D050'],   # Early green
                    [0.1, '#80FF80'],    # GREEN END - Acceptable degradation (shrunk)
                    [0.2, '#99FF99'],    # Green to yellow transition
                    [0.3, '#CCFF88'],    # Yellow-green - caution zone
                    [0.4, '#FFFF66'],    # Yellow - approaching problem
                    [0.5, '#FFD700'],    # Gold - broadcast quality concern
                    [0.6, '#FFA500'],    # Orange start - quality degraded
                    [0.7, '#FF8C00'],    # Orange mid - stretched orange range
                    [0.8, '#FF6347'],    # Orange-red - significant impact
                    [0.85, '#FF4500'],   # Red - major quality loss
                    [0.9, '#E60000'],    # Deep red - severe degradation
                    [0.95, '#CC0000'],   # Dark red - critical failure
                    [1.0, '#B30000']     # Darkest red - unacceptable
                ],
                hovertemplate="<b>%{y}</b><br>" +
                              "Frequency: %{x}<br>" +
                              "STI Degradation: %{z:.1f}%<br>" +
                              "<extra></extra>",
                colorbar=dict(
                    title="STI Degradation (%)",
                    tickmode="linear",
                    tick0=0,
                    dtick=10
                ),
                zmin=0,      # No degradation
                zmax=50      # Maximum expected degradation
            ))
            
            fig.update_layout(
                title="STI Degradation Heatmap by Position & Frequency (Before Treatment)",
                xaxis_title="",
                yaxis_title="Measurement Position",
                height=500,
                annotations=[
                    dict(
                        text="Data Source: data/raw/250715-smaartLogs/Std8/*.txt | Reference: HostA STI",
                        xref="paper", yref="paper",
                        x=0.02, y=0.98,
                        showarrow=False,
                        font=dict(size=10, color="gray")
                    )
                ]
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error loading Smaart STI data: {e}")
            return None
    
    def create_adjusted_degradation_heatmap(self, panel_count):
        """Create STI degradation heatmap showing improvement with acoustic treatment"""
        
        try:
            # Try multiple possible paths for smaart data
            possible_smaart_paths = [
                Path('data/raw/250715-smaartLogs/Std8'),
                self.base_path / 'data/raw/250715-smaartLogs/Std8',
                Path('/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard/data/raw/250715-smaartLogs/Std8')
            ]
            
            smaart_path = None
            for path in possible_smaart_paths:
                if path.exists():
                    smaart_path = path
                    break
            
            if smaart_path is None:
                st.error("Smaart data directory not found")
                return None
            
            # Load treatment priority data with multiple possible paths
            possible_priority_paths = [
                self.base_path / 'data/generated/250728-Studio8-Treatment_Priority_Matrix.csv',
                Path('data/generated/250728-Studio8-Treatment_Priority_Matrix.csv'),
                Path('/Users/chrislyons/Documents/CL/dev/std8/cbc-interactive-dashboard/data/generated/250728-Studio8-Treatment_Priority_Matrix.csv')
            ]
            
            priority_df = None
            for priority_file in possible_priority_paths:
                if priority_file.exists():
                    priority_df = pd.read_csv(priority_file)
                    break
            
            if priority_df is None:
                st.error("Treatment priority data not found")
                return None
            
            # File mapping to positions
            file_mapping = {
                'Std8-HostA-128k-Sweep.txt': 'HostA (Reference)',
                'Std8-HostC-128k-Sweep.txt': 'HostC (Talent)',
                'Std8-Ceiling-128k-Sweep.txt': 'Ceiling',
                'Std8-MidRoom-128k-Sweep.txt': 'MidRoom',
                'Std8-NECorner-High-128k-Sweep.txt': 'NECorner-High',
                'Std8-NECorner-Low-128k-Sweep.txt': 'NECorner-Low',
                'Std8-SECorner-128k-Sweep.txt': 'SECorner',
                'Std8-SWCorner-128k-Sweep.txt': 'SWCorner'
            }
            
            # STI frequency bands available in Smaart data
            sti_freq_bands = [125, 250, 500, 1000, 2000, 4000, 8000]
            freq_labels = [f"{f}Hz" if f < 1000 else f"{f/1000:.0f}kHz" for f in sti_freq_bands]
            
            positions = []
            sti_matrix = []
            reference_sti = None
            
            # Get reference STI values from HostA
            ref_filepath = smaart_path / 'Std8-HostA-128k-Sweep.txt'
            if ref_filepath.exists():
                with open(ref_filepath, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.startswith('STI\t'):
                        parts = line.strip().split('\t')
                        if len(parts) >= 8:
                            reference_sti = [float(parts[i]) for i in range(2, 9)]
                            break
            
            if not reference_sti:
                st.error("Could not load reference STI data from HostA")
                return None
            
            # Calculate treatment effectiveness based on priority and panel count
            position_priority = {}
            for _, row in priority_df.iterrows():
                pos_name = row['position']
                priority_score = row['priority_score']
                position_priority[pos_name] = priority_score
            
            # Sort positions by priority for panel allocation
            sorted_priorities = sorted(position_priority.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate panel allocation per position based on priority
            panels_per_position = {}
            remaining_panels = panel_count
            
            # For low panel counts, distribute more evenly
            if panel_count <= 15:
                # Distribute panels one by one to highest priority positions first
                for pos_name, priority in sorted_priorities:
                    panels_per_position[pos_name] = 0
                
                # Distribute remaining panels one at a time to highest priority positions
                for i in range(panel_count):
                    if i < len(sorted_priorities):
                        pos_name = sorted_priorities[i % len(sorted_priorities)][0]
                        panels_per_position[pos_name] += 1
            else:
                # Original allocation for higher panel counts
                for pos_name, priority in sorted_priorities:
                    if remaining_panels <= 0:
                        panels_per_position[pos_name] = 0
                        continue
                        
                    # High priority positions get more panels
                    if priority >= 6.0:
                        allocated = min(6, remaining_panels)
                    elif priority >= 5.0:
                        allocated = min(4, remaining_panels)
                    elif priority >= 4.0:
                        allocated = min(3, remaining_panels)
                    else:
                        allocated = min(2, remaining_panels)
                    
                    panels_per_position[pos_name] = allocated
                    remaining_panels -= allocated
            
            # Process each position for STI improvement
            for filename, position_name in file_mapping.items():
                filepath = smaart_path / filename
                if not filepath.exists():
                    continue
                    
                positions.append(position_name)
                
                # Parse Smaart file for STI data
                sti_values = None
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                    
                for line in lines:
                    if line.startswith('STI\t'):
                        parts = line.strip().split('\t')
                        if len(parts) >= 8:
                            sti_values = [float(parts[i]) for i in range(2, 9)]
                            break
                
                if sti_values:
                    # Get position name for priority lookup
                    lookup_name = position_name.replace(' (Reference)', '').replace(' (Talent)', '')
                    
                    # Calculate STI improvement based on panels allocated
                    panel_allocation = panels_per_position.get(lookup_name, 0)
                    
                    # STI improvement per panel (empirically derived from acoustic theory)
                    # Higher frequencies benefit more from absorption treatment
                    improvement_per_panel = [0.015, 0.018, 0.022, 0.025, 0.030, 0.028, 0.025]  # Per frequency band
                    
                    # Apply treatment effect
                    improved_sti = []
                    for i, (original_sti, ref_sti, improvement_rate) in enumerate(zip(sti_values, reference_sti, improvement_per_panel)):
                        # Calculate improvement (diminishing returns)
                        improvement = improvement_rate * panel_allocation * (1 - panel_allocation/40)  # Diminishing returns
                        new_sti = min(ref_sti, original_sti + improvement)  # Can't exceed reference
                        improved_sti.append(new_sti)
                    
                    # Calculate new degradation percentages
                    sti_degradation_row = []
                    for i, (sti_val, ref_val) in enumerate(zip(improved_sti, reference_sti)):
                        if ref_val > 0:
                            degradation_percent = ((ref_val - sti_val) / ref_val) * 100
                            sti_degradation_row.append(max(0, degradation_percent))
                        else:
                            sti_degradation_row.append(0)
                    
                    sti_matrix.append(sti_degradation_row)
                else:
                    sti_matrix.append([0] * len(sti_freq_bands))
            
            # Create heatmap with same colorscale as original
            fig = go.Figure(data=go.Heatmap(
                z=sti_matrix,
                x=freq_labels,
                y=positions,
                colorscale=[
                    [0.0, '#40C040'],    # GREEN START - No degradation (ideal)
                    [0.05, '#50D050'],   # Early green
                    [0.1, '#80FF80'],    # GREEN END - Acceptable degradation (shrunk)
                    [0.2, '#99FF99'],    # Green to yellow transition
                    [0.3, '#CCFF88'],    # Yellow-green - caution zone
                    [0.4, '#FFFF66'],    # Yellow - approaching problem
                    [0.5, '#FFD700'],    # Gold - broadcast quality concern
                    [0.6, '#FFA500'],    # Orange start - quality degraded
                    [0.7, '#FF8C00'],    # Orange mid - stretched orange range
                    [0.8, '#FF6347'],    # Orange-red - significant impact
                    [0.85, '#FF4500'],   # Red - major quality loss
                    [0.9, '#E60000'],    # Deep red - severe degradation
                    [0.95, '#CC0000'],   # Dark red - critical failure
                    [1.0, '#B30000']     # Darkest red - unacceptable
                ],
                hovertemplate="<b>%{y}</b><br>" +
                              "Frequency: %{x}<br>" +
                              "STI Degradation: %{z:.1f}%<br>" +
                              "<extra></extra>",
                colorbar=dict(
                    title="STI Degradation (%)",
                    tickmode="linear",
                    tick0=0,
                    dtick=10
                ),
                zmin=0,      # No degradation
                zmax=50      # Maximum expected degradation
            ))
            
            fig.update_layout(
                title="STI Degradation Heatmap by Position & Frequency (After Treatment)",
                xaxis_title="",
                yaxis_title="Measurement Position",
                height=500,
                annotations=[
                    dict(
                        text=f"Treatment Simulation: {panel_count} panels allocated by priority",
                        xref="paper", yref="paper",
                        x=0.02, y=0.98,
                        showarrow=False,
                        font=dict(size=10, color="gray")
                    )
                ]
            )
            
            return fig
            
        except Exception as e:
            st.error(f"Error creating adjusted STI heatmap: {e}")
            return None
    
    def render_frequency_explorer(self, space="Studio 8"):
        """Main function to render the frequency response explorer"""
        
        # Two-column header layout with vertical alignment
        header_col1, header_col2 = st.columns([1, 1])
        
        with header_col1:
            # Initialize analysis type in session state for persistence across space changes
            if "freq_analysis_type" not in st.session_state:
                st.session_state.freq_analysis_type = "STI Degradation Heatmap"
            
            # Main page analysis selector with persistence - conditional options based on space
            if hasattr(st.session_state, 'selected_space') and st.session_state.selected_space == "The Hub":
                # Hide STI options for The Hub (no STI data available)
                analysis_options = ["Magnitude Response", "Phase Response", "Modal Stack Analysis"]
                # Reset to valid option if currently on STI
                if st.session_state.freq_analysis_type == "STI Degradation Heatmap":
                    st.session_state.freq_analysis_type = "Magnitude Response"
            else:
                # Full options for Studio 8
                analysis_options = ["STI Degradation Heatmap", "Magnitude Response", "Phase Response", "Modal Stack Analysis"]
            
            current_index = analysis_options.index(st.session_state.freq_analysis_type) if st.session_state.freq_analysis_type in analysis_options else 0
            
            analysis_type = st.selectbox(
                "Select Analysis View:",
                analysis_options,
                index=current_index,
                help="Choose which analysis to display",
                key="freq_analysis_selector"
            )
            # Add delay for smoothness
            import time
            time.sleep(0.05)
            
            # Update session state when selection changes
            st.session_state.freq_analysis_type = analysis_type
        
        with header_col2:
            if analysis_type == "STI Degradation Heatmap":
                # Initialize panel count in session state with space-specific defaults
                if 'panel_count' not in st.session_state:
                    current_space = getattr(st.session_state, 'selected_space', 'Studio 8')
                    default_count = 8 if current_space == "The Hub" else 25
                    st.session_state.panel_count = default_count
                
                # Panel count text input with space-specific max values
                current_space = getattr(st.session_state, 'selected_space', 'Studio 8')
                max_panels = 16 if current_space == "The Hub" else 32
                
                # Reset panel count if it exceeds the current space's maximum
                if st.session_state.panel_count > max_panels:
                    default_count = 8 if current_space == "The Hub" else 25
                    st.session_state.panel_count = default_count
                
                current_panel_count = st.number_input(
                    label="Panel Count",
                    min_value=0,
                    max_value=max_panels,
                    value=st.session_state.panel_count,
                    step=1,
                    key="panel_number_input",
                    help=f"Enter panel count directly (max {max_panels} for {current_space})"
                )
                # Add delay for smoothness
                import time
                time.sleep(0.05)
                # Update session state with typed value
                st.session_state.panel_count = current_panel_count
            else:
                # Add vertical spacing to align with dropdown label
                st.markdown('<div style="margin-top: 0.5rem;"></div>', unsafe_allow_html=True)
                # Page disclaimer for other analysis types
                st.info("**📊 Test data below reflects the present state of this production space prior to panel treatment.**")
                # Set default panel count for other views
                current_panel_count = st.session_state.get('panel_count', 25)
        
        # Load data for the specified space
        data_loaded = self.load_smaart_data(space)
        
        # Control panel in sidebar (simplified)
        with st.sidebar:
            st.subheader("Analysis Controls")
            
            # Only show frequency range control for frequency response views
            if analysis_type in ["Magnitude Response", "Phase Response"]:
                # Frequency range control - simple number inputs with Hz values
                st.markdown("**Frequency Range**")
                
                col1, col2 = st.columns(2)
                with col1:
                    freq_min = st.number_input(
                        "Min Hz",
                        min_value=30,
                        max_value=2999,
                        value=30,
                        step=10
                    )
                    # Add delay for smoothness
                    import time
                    time.sleep(0.05)
                with col2:
                    freq_max = st.number_input(
                        "Max Hz",
                        min_value=freq_min + 10,
                        max_value=3000,
                        value=3000,
                        step=100
                    )
                    # Add delay for smoothness
                    import time
                    time.sleep(0.05)
                
                freq_range = (freq_min, freq_max)
            else:
                # Default frequency range for other analysis types
                freq_range = (30, 3000)
        
        # Main visualization area - single view with increased height
        if analysis_type == "STI Degradation Heatmap":
            
            # Two-column layout for before/after comparison
            col1, col2 = st.columns(2)
            
            with col1:
                fig_heatmap_before = self.create_degradation_heatmap()
                # Increase height for single view
                fig_heatmap_before.update_layout(height=600)
                st.plotly_chart(fig_heatmap_before, use_container_width=True)
            
            with col2:
                fig_heatmap_after = self.create_adjusted_degradation_heatmap(current_panel_count)
                if fig_heatmap_after is not None:
                    # Increase height for single view
                    fig_heatmap_after.update_layout(height=600)
                    st.plotly_chart(fig_heatmap_after, use_container_width=True)
                else:
                    st.error("Unable to generate adjusted heatmap - check data files")
        
        elif analysis_type == "Magnitude Response":
            fig_mag = self.create_magnitude_response_plot(freq_range)
            st.plotly_chart(fig_mag, use_container_width=True)
        
        elif analysis_type == "Phase Response":
            fig_phase = self.create_phase_response_plot(freq_range)
            st.plotly_chart(fig_phase, use_container_width=True)
        
        elif analysis_type == "Modal Stack Analysis":
            fig_modal = self.create_modal_analysis_plot(space)
            # Set height for single view
            fig_modal.update_layout(height=800)
            st.plotly_chart(fig_modal, use_container_width=True)
        
        # Analysis insights
        with st.expander("🔍 Analysis Insights"):
            if self.measurement_positions:
                st.write("**Key Findings:**")
                
                # Find worst position
                worst_pos = max(self.measurement_positions.items(), key=lambda x: x[1]['degradation'])
                st.write(f"- **Worst Performance:** {worst_pos[0]} ({worst_pos[1]['degradation']:.1f}% STI degradation)")
                
                # Find best position (excluding reference)
                non_ref_positions = {k: v for k, v in self.measurement_positions.items() if 'Reference' not in k}
                if non_ref_positions:
                    best_pos = min(non_ref_positions.items(), key=lambda x: x[1]['degradation'])
                    st.write(f"- **Best Performance:** {best_pos[0]} ({best_pos[1]['degradation']:.1f}% STI degradation)")
                
                # Average metrics
                avg_sti = np.mean([p['STI'] for p in self.measurement_positions.values() if 'Reference' not in p])
                avg_rt60 = np.mean([p['RT60'] for p in self.measurement_positions.values() if 'Reference' not in p])
                st.write(f"- **Average STI:** {avg_sti:.2f} (Target: >0.75)")
                st.write(f"- **Average RT60:** {avg_rt60:.2f}s (Target: 0.3-0.5s)")

if __name__ == "__main__":
    explorer = FrequencyResponseExplorer()
    explorer.render_frequency_explorer()