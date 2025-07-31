#!/usr/bin/env python3
"""
Enhanced 3D Room Visualizer with Acoustic Panel Placement
Creates detailed 3D models showing treatment recommendations
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pathlib import Path
import pandas as pd

class Enhanced3DVisualizer:
    def __init__(self):
        self.colors = {
            'room_structure': '#2c3e50',
            'zone_a': 'rgba(52, 152, 219, 0.3)',
            'zone_b': 'rgba(241, 196, 15, 0.2)',
            'measurement_pos': '#e74c3c',
            'reference_pos': '#27ae60',
            'absorption_panel': '#8e44ad',
            'bass_trap': '#d35400',
            'hallway': 'rgba(200, 200, 200, 0.4)'
        }
    
    def create_studio8_detailed_model(self, show_panels=True, panel_count=25):
        """Create detailed Studio 8 model with treatment visualization"""
        
        # Room dimensions (feet) - CORRECTED ORIENTATION
        # North-South = short walls (23'-4½"), East-West = long walls (27'-5")
        room_width_EW = 23.375  # 23'-4½" East-West direction (short walls)
        room_length_NS = 27.42  # 27'-5" North-South direction (long walls)
        height = 14
        grid_height = 10
        
        fig = go.Figure()
        
        # Room structure
        self._add_room_structure(fig, room_width_EW, room_length_NS, height)
        
        # Add hallway along E wall
        self._add_hallway(fig, room_width_EW, room_length_NS, height)
        
        # Lighting grid plane
        self._add_lighting_grid(fig, room_width_EW, room_length_NS, grid_height)
        
        # Measurement positions
        # Desk center after rotation and move: x=11.6875, y=8.71 
        desk_center_x = room_width_EW/2
        desk_center_y = (room_length_NS/2) - 5
        
        positions = {
            "Host A (Reference)": {"coords": [desk_center_x + 4, desk_center_y - 2, 5.5], "color": self.colors['reference_pos'], "size": 10},  # SE corner of desk
            "Host C (Talent)": {"coords": [desk_center_x - 4, desk_center_y - 2, 5.5], "color": "blue", "size": 8},    # SW corner of desk
            "Mid Room": {"coords": [desk_center_x, desk_center_y + 8, 5.5], "color": self.colors['measurement_pos'], "size": 8},           # 8' north of desk center
            "NE Corner": {"coords": [20.5, 24.9, 11.5], "color": self.colors['measurement_pos'], "size": 8},
            "SE Corner": {"coords": [19.5, 2.5, 7.5], "color": self.colors['measurement_pos'], "size": 8},
            "SW Corner": {"coords": [5.2, 3.9, 5.5], "color": self.colors['measurement_pos'], "size": 8},
            "NW Corner": {"coords": [5.2, 23.5, 5.5], "color": self.colors['measurement_pos'], "size": 8},
            "Ceiling": {"coords": [5.2, 3.9, 12], "color": self.colors['measurement_pos'], "size": 8}
        }
        
        self._add_measurement_positions(fig, positions)
        
        # Add human figures for hosts (commented out for now)
        # self._add_human_figures(fig, positions)
        
        # Add acoustic treatment panels if requested
        if show_panels:
            self._add_treatment_panels_studio8(fig, panel_count, room_width_EW, room_length_NS, height, grid_height)
        
        # Add furniture and equipment
        self._add_studio8_furniture(fig, room_width_EW, room_length_NS)
        
        # Add wall labels with better visibility - moved further outward and to floor level to reduce visual clutter
        # Add red circles around cardinal direction markers
        import numpy as np
        circle_points = 20
        circle_radius = 1.5
        theta = np.linspace(0, 2*np.pi, circle_points)
        circle_x = circle_radius * np.cos(theta)
        circle_y = circle_radius * np.sin(theta)
        circle_z = np.zeros(circle_points)
        
        # West circle and text
        # fig.add_trace(go.Scatter3d(
        #     x=circle_x + (-5), y=circle_y + (room_length_NS/2), z=circle_z,
        #     mode='lines', line=dict(color='red', width=1),
        #     showlegend=False, hoverinfo='skip'
        # ))
        fig.add_trace(go.Scatter3d(
            x=[-5], y=[room_length_NS/2], z=[0],
            mode='text', text=["W"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # East circle and text
        # fig.add_trace(go.Scatter3d(
        #     x=circle_x + (room_width_EW+5), y=circle_y + (room_length_NS/2), z=circle_z,
        #     mode='lines', line=dict(color='red', width=1),
        #     showlegend=False, hoverinfo='skip'
        # ))
        fig.add_trace(go.Scatter3d(
            x=[room_width_EW+5], y=[room_length_NS/2], z=[0],
            mode='text', text=["E"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # South circle and text
        # fig.add_trace(go.Scatter3d(
        #     x=circle_x + (room_width_EW/2), y=circle_y + (-5), z=circle_z,
        #     mode='lines', line=dict(color='red', width=1),
        #     showlegend=False, hoverinfo='skip'
        # ))
        fig.add_trace(go.Scatter3d(
            x=[room_width_EW/2], y=[-5], z=[0],
            mode='text', text=["S"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # North circle and text
        # fig.add_trace(go.Scatter3d(
        #     x=circle_x + (room_width_EW/2), y=circle_y + (room_length_NS+5), z=circle_z,
        #     mode='lines', line=dict(color='red', width=1),
        #     showlegend=False, hoverinfo='skip'
        # ))
        fig.add_trace(go.Scatter3d(
            x=[room_width_EW/2], y=[room_length_NS+5], z=[0],
            mode='text', text=["N"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        fig.update_layout(
            title="Studio 8 - Detailed 3D Model with Acoustic Treatment",
            scene=dict(
                xaxis_title="(feet)",
                yaxis_title="(feet)", 
                zaxis_title="Height (feet)",
                camera=dict(eye=dict(x=1.05, y=1.25, z=0.005)),
                aspectmode='data'
            ),
            height=700,
            showlegend=False,  # Hide legend completely
            margin=dict(l=20, r=20, t=60, b=20)  # Center the viewer with balanced margins
        )
        
        return fig
    
    def create_studio8_with_modal_analysis(self, show_panels=True, panel_count=25, show_zone_a=True, show_zone_b=True):
        """Create Studio 8 model with modal stack visualization overlay"""
        
        # Create base model
        fig = self.create_studio8_detailed_model(show_panels=show_panels, panel_count=panel_count)
        
        # Add modal visualization
        fig = self.add_modal_visualization(fig, show_zone_a=show_zone_a, show_zone_b=show_zone_b)
        
        # Update title
        fig.update_layout(
            title="Studio 8 - 3D Model with Zone A/B Modal Stack Analysis"
        )
        
        return fig
    
    def add_modal_visualization(self, fig, show_zone_a=True, show_zone_b=True):
        """Add color-coded modal stack visualization for Zone A and Zone B"""
        
        # Room dimensions
        room_width_EW = 23.375  # 23'-4½" East-West
        room_length_NS = 27.42  # 27'-5" North-South
        height = 14
        grid_height = 10
        
        # Empirically confirmed resonant peaks in Studio 8
        modal_frequencies = [23.1, 29.1, 37.8, 50.0, 63.0, 74.3, 108.3, 152.8, 206.8, 258.8, 317.9, 448.4, 561.2, 679.0]
        
        # Zone definitions
        zone_a_height = grid_height  # Below lighting grid (0 to 10')
        zone_b_height = height - grid_height  # Above lighting grid (10' to 14')
        
        # Color coding
        zone_a_color = 'rgba(255, 100, 100, 0.6)'  # Red for Zone A (Set Volume)
        zone_b_color = 'rgba(100, 100, 255, 0.6)'  # Blue for Zone B (Ceiling Cavity)
        
        if show_zone_a:
            # Zone A modal visualization - focused on lower frequencies that are more problematic
            zone_a_modes = [f for f in modal_frequencies if f <= 150]  # Lower frequencies more critical in Zone A
            zone_a_legend_shown = False
            
            for i, freq in enumerate(zone_a_modes):
                # Calculate wavelength and position modal visualization
                wavelength = 343 / freq  # c = 343 m/s at 20°C
                wavelength_ft = wavelength * 3.28084  # Convert to feet
                
                # Create modal pressure visualization as translucent rectangles
                # Position based on room mode patterns
                if freq <= 50:  # Very low frequency modes - room-wide patterns
                    modal_height = zone_a_height * 0.8
                    modal_positions = [
                        [room_width_EW/4, room_length_NS/4, modal_height/2],
                        [3*room_width_EW/4, room_length_NS/4, modal_height/2],
                        [room_width_EW/4, 3*room_length_NS/4, modal_height/2],
                        [3*room_width_EW/4, 3*room_length_NS/4, modal_height/2]
                    ]
                elif freq <= 100:  # Mid-low frequencies - more localized patterns
                    modal_height = zone_a_height * 0.6
                    modal_positions = [
                        [room_width_EW/3, room_length_NS/3, modal_height/2],
                        [2*room_width_EW/3, 2*room_length_NS/3, modal_height/2]
                    ]
                else:  # Higher frequencies - more focused around listening area
                    modal_height = zone_a_height * 0.4
                    desk_center_x = room_width_EW/2
                    desk_center_y = (room_length_NS/2) - 5
                    modal_positions = [
                        [desk_center_x, desk_center_y, modal_height/2]
                    ]
                
                # Add modal visualization traces
                for pos in modal_positions:
                    x, y, z = pos
                    size = max(3, min(12, wavelength_ft/2))  # Size based on wavelength
                    
                    show_in_legend = not zone_a_legend_shown
                    if show_in_legend:
                        zone_a_legend_shown = True
                    
                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z],
                        mode='markers',
                        marker=dict(
                            size=size,
                            color=zone_a_color,
                            symbol='circle',
                            opacity=0.7,
                            line=dict(width=2, color='darkred')
                        ),
                        name='Zone A Modals' if show_in_legend else f'Zone A Modal: {freq}Hz',
                        legendgroup='Zone A Modals',
                        showlegend=show_in_legend,
                        hovertemplate=f"<b>Zone A Modal</b><br>" +
                                    f"Frequency: {freq} Hz<br>" +
                                    f"Wavelength: {wavelength_ft:.1f} ft<br>" +
                                    f"Position: ({x:.1f}', {y:.1f}', {z:.1f}')<br>" +
                                    "<extra></extra>"
                    ))
        
        if show_zone_b:
            # Zone B modal visualization - ceiling cavity modes
            zone_b_modes = [f for f in modal_frequencies if f >= 100]  # Higher frequencies more relevant in smaller Zone B
            zone_b_legend_shown = False
            
            for i, freq in enumerate(zone_b_modes):
                # Calculate wavelength
                wavelength = 343 / freq
                wavelength_ft = wavelength * 3.28084
                
                # Zone B positioning - above lighting grid
                modal_z = grid_height + (zone_b_height * 0.5)  # Middle of Zone B
                
                # Smaller cavity means more concentrated modal patterns
                if freq <= 200:  # Lower Zone B frequencies - broader patterns
                    modal_positions = [
                        [room_width_EW/3, room_length_NS/3, modal_z],
                        [2*room_width_EW/3, 2*room_length_NS/3, modal_z]
                    ]
                elif freq <= 400:  # Mid Zone B frequencies
                    modal_positions = [
                        [room_width_EW/2, room_length_NS/2, modal_z]
                    ]
                else:  # Higher frequencies - more dispersed
                    modal_positions = [
                        [room_width_EW * 0.4, room_length_NS * 0.4, modal_z],
                        [room_width_EW * 0.6, room_length_NS * 0.6, modal_z]
                    ]
                
                # Add Zone B modal visualization
                for pos in modal_positions:
                    x, y, z = pos
                    size = max(2, min(8, wavelength_ft/3))  # Smaller sizes for higher frequencies
                    
                    show_in_legend = not zone_b_legend_shown
                    if show_in_legend:
                        zone_b_legend_shown = True
                    
                    fig.add_trace(go.Scatter3d(
                        x=[x], y=[y], z=[z],
                        mode='markers',
                        marker=dict(
                            size=size,
                            color=zone_b_color,
                            symbol='diamond',
                            opacity=0.7,
                            line=dict(width=2, color='darkblue')
                        ),
                        name='Zone B Modals' if show_in_legend else f'Zone B Modal: {freq}Hz',
                        legendgroup='Zone B Modals',
                        showlegend=show_in_legend,
                        hovertemplate=f"<b>Zone B Modal</b><br>" +
                                    f"Frequency: {freq} Hz<br>" +
                                    f"Wavelength: {wavelength_ft:.1f} ft<br>" +
                                    f"Position: ({x:.1f}', {y:.1f}', {z:.1f}')<br>" +
                                    "<extra></extra>"
                    ))
        
        # Add zone boundary visualization
        if show_zone_a and show_zone_b:
            # Add lighting grid plane as zone boundary
            x_grid = np.linspace(0, room_width_EW, 20)
            y_grid = np.linspace(0, room_length_NS, 15)
            X, Y = np.meshgrid(x_grid, y_grid)
            Z = np.full_like(X, grid_height)
            
            fig.add_trace(go.Surface(
                x=X, y=Y, z=Z,
                colorscale=[[0, 'rgba(100, 100, 100, 0.1)'], [1, 'rgba(100, 100, 100, 0.1)']],
                opacity=0.2,
                name='Zone A/B Boundary',
                showlegend=True,
                showscale=False,
                hovertemplate="Zone A/B Boundary<br>Height: 10' (Lighting Grid)<extra></extra>"
            ))
        
        return fig
    
    def create_hub_detailed_model(self, show_panels=True, panel_count=10):
        """Create detailed Hub model with treatment visualization based on corrected actual measurements"""
        
        # Hub dimensions from corrected measurements (converting inches to feet)
        # Based on actual measurements: Red 83", Blue 104", Green 72", Purple 140", Orange 60", Orange>Red 246"
        ceiling_height = 106 / 12.0  # 106" = 8.83 feet to hung ceiling
        grid_height = 101 / 12.0     # 101" = 8.42 feet to grid
        
        fig = go.Figure()
        
        # Add accurate Hub room structure based on corrected measurements
        self._add_hub_structure_corrected(fig, ceiling_height, grid_height)
        
        # Measurement positions for Hub based on PDF floorplan layout
        positions = {
            "MidRoom": {"coords": [0, 0, 6], "color": self.colors['reference_pos'], "size": 10},
            "BackCorner": {"coords": [-6, -2, 6], "color": self.colors['measurement_pos'], "size": 8},
            "Chair1": {"coords": [-4.5, 0.5, 4], "color": "blue", "size": 8},  # In set build area (left side)
            "Chair2": {"coords": [-3.5, 1.5, 4], "color": "green", "size": 8},  # In set build area (left side)  
            "CeilingCorner": {"coords": [5, 1, 10], "color": self.colors['measurement_pos'], "size": 8}
        }
        
        # Hide measurement positions for now - will fix later
        # self._add_measurement_positions(fig, positions)
        
        # Add acoustic treatment panels if requested
        if show_panels:
            self._add_treatment_panels_hub_corrected(fig, panel_count, ceiling_height, grid_height)
        
        # Hide set build furniture for now - will fix later  
        # self._add_hub_furniture_corrected(fig)
        
        fig.update_layout(
            title="The Hub - Detailed 3D Model with Acoustic Treatment (Corrected Dimensions)",
            scene=dict(
                xaxis_title="(feet)",
                yaxis_title="(feet)", 
                zaxis_title="Height (feet)",
                camera=dict(eye=dict(x=1.2, y=1.5, z=0.8)),
                aspectmode='data'
            ),
            height=700,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig
    
    def _add_hub_structure_corrected(self, fig, ceiling_height, grid_height):
        """Add Hub room structure based on corrected actual measurements"""
        import numpy as np
        
        # Convert measurements from inches to feet for coordinate system
        # Cardinal directions: NORTH=Red 83", NORTHWEST=Blue 104", WEST=Orange>Red 246" (glass wall), SOUTHWEST=Purple 140", SOUTH=Orange 60", EAST=Green 72"
        north = 83 / 12.0      # 6.92 feet (Red wall)
        northwest = 104 / 12.0 # 8.67 feet (Blue wall)
        west = 246 / 12.0      # 20.50 feet (Orange>Red glass wall - curves outward)
        southwest = 140 / 12.0 # 11.67 feet (Purple wall)
        south = 60 / 12.0      # 5.00 feet (Orange wall)
        east = 72 / 12.0       # 6.00 feet (Green wall)
        
        # The Hub is an irregular hexagonal shape based on your diagram
        # Working from your corrected measurements and the photo view from the doorway (orange wall)
        # Creating vertices starting from the orange wall (bottom) and going clockwise
        
        # Place origin at approximate center of the space for better visualization
        center_x = 0
        center_y = 0
        
        # Starting from south wall (bottom, facing into room from doorway) and going clockwise
        # The room is wider at the southwest (purple wall area) and narrows toward the south
        hub_vertices = [
            # South wall (bottom) - 60" wide
            [-south/2, -southwest/2 + 2],      # Bottom left of south wall
            [south/2, -southwest/2 + 2],       # Bottom right of south wall
            
            # Transition to east side - North wall area (83")  
            [south/2 + 2, -southwest/2 + 2 + north/3],    # Start of east angled wall
            [south/2 + 3, -southwest/2 + 2 + 2*north/3],  # Mid east angled wall
            [south/2 + 2, -southwest/2 + 2 + north],      # End of east angled wall
            
            # WEST wall (Orange>Red 246") - bisected into three sections
            # This is the Southwest wall area (140" - the longest dimension) 
            [southwest/2, east/2],                              # Right end of west wall
            
            # Section 1: Right third to middle (diagonal connection)
            [southwest/4, east/2 + 1],                          # First diagonal section
            
            # Section 2: Middle section moved outward by 2 feet  
            [0, east/2 + 2],                                    # Middle section bulges out 2 feet
            
            # Section 3: Middle to left third (diagonal connection)
            [-southwest/4, east/2 + 1],                         # Second diagonal section
            
            [-southwest/2, east/2],                             # Left end of west wall  
            
            # Left side transition - Northwest area (104")
            [-south/2 - 3, -southwest/2 + 2 + northwest/2],  # Left angled wall
            [-south/2 - 2, -southwest/2 + 2 + northwest/4],  # Left angled wall continuation
        ]
        
        # Close the shape
        hub_x = [v[0] for v in hub_vertices] + [hub_vertices[0][0]]
        hub_y = [v[1] for v in hub_vertices] + [hub_vertices[0][1]]
        hub_z = [0] * len(hub_x)
        
        # Floor outline
        fig.add_trace(go.Scatter3d(
            x=hub_x, y=hub_y, z=hub_z,
            mode='lines',
            line=dict(color=self.colors['room_structure'], width=6),
            name='Hub Floor Outline',
            showlegend=False
        ))
        
        # Ceiling outline
        ceiling_z = [ceiling_height] * len(hub_x)
        fig.add_trace(go.Scatter3d(
            x=hub_x, y=hub_y, z=ceiling_z,
            mode='lines',
            line=dict(color=self.colors['room_structure'], width=6),
            name='Hub Ceiling Outline',
            showlegend=False
        ))
        
        # Vertical edges with door opening on north wall
        for i in range(len(hub_x)-1):  # -1 because last point duplicates first
            # Skip vertical edge where door opening should be (between points 4 and 5 on north wall)
            if i == 4:  # This is the north wall area where door opening is
                # Add door opening by creating partial vertical edges
                door_height = 7  # 7 feet high door
                
                # Vertical edge up to door height
                fig.add_trace(go.Scatter3d(
                    x=[hub_x[i], hub_x[i]], 
                    y=[hub_y[i], hub_y[i]], 
                    z=[0, door_height],
                    mode='lines',
                    line=dict(color=self.colors['room_structure'], width=4),
                    showlegend=False
                ))
                
                # Vertical edge from door top to ceiling
                fig.add_trace(go.Scatter3d(
                    x=[hub_x[i], hub_x[i]], 
                    y=[hub_y[i], hub_y[i]], 
                    z=[door_height, ceiling_height],
                    mode='lines',
                    line=dict(color=self.colors['room_structure'], width=4),
                    showlegend=False
                ))
                
                # Door frame top (horizontal)
                fig.add_trace(go.Scatter3d(
                    x=[hub_x[i], hub_x[i+1]], 
                    y=[hub_y[i], hub_y[i+1]], 
                    z=[door_height, door_height],
                    mode='lines',
                    line=dict(color=self.colors['room_structure'], width=4),
                    showlegend=False
                ))
            else:
                # Normal vertical edge
                fig.add_trace(go.Scatter3d(
                    x=[hub_x[i], hub_x[i]], 
                    y=[hub_y[i], hub_y[i]], 
                    z=[0, ceiling_height],
                    mode='lines',
                    line=dict(color=self.colors['room_structure'], width=4),
                    showlegend=False
                ))
        
        # Add pipe grid at corrected height (101" = 8.42 feet) - shown as translucent plane
        grid_x = np.linspace(min(hub_x), max(hub_x), 10)
        grid_y = np.linspace(min(hub_y), max(hub_y), 8)
        X, Y = np.meshgrid(grid_x, grid_y)
        Z = np.full_like(X, grid_height)
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale=[[0, 'rgba(0, 255, 0, 0.2)'], [1, 'rgba(0, 255, 0, 0.2)']],
            opacity=0.3,
            name=f'Pipe Grid (101" = {grid_height:.1f}\')',
            showlegend=True,
            showscale=False,
            hovertemplate=f"Pipe Grid<br>Height: 101\" ({grid_height:.1f}')<extra></extra>"
        ))
        
        # Add cardinal direction labels at floor level, hovering outside the space
        # Calculate approximate center and extents of the Hub
        center_x = sum(hub_x[:-1]) / len(hub_x[:-1])  # Exclude duplicate closing point
        center_y = sum(hub_y[:-1]) / len(hub_y[:-1])
        max_x = max(hub_x)
        min_x = min(hub_x)
        max_y = max(hub_y)
        min_y = min(hub_y)
        
        # North (Red letters) - rotated 90deg clockwise
        fig.add_trace(go.Scatter3d(
            x=[max_x + 3], y=[center_y], z=[0],
            mode='text', text=["N"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # East (Red letters) - rotated 90deg clockwise
        fig.add_trace(go.Scatter3d(
            x=[center_x], y=[min_y - 3], z=[0],
            mode='text', text=["E"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # South (Red letters) - rotated 90deg clockwise
        fig.add_trace(go.Scatter3d(
            x=[min_x - 3], y=[center_y], z=[0],
            mode='text', text=["S"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
        
        # West (Red letters) - rotated 90deg clockwise
        fig.add_trace(go.Scatter3d(
            x=[center_x], y=[max_y + 3], z=[0],
            mode='text', text=["W"], textfont=dict(size=18, color='red'),
            showlegend=False, hoverinfo='skip'
        ))
    
    def _add_treatment_panels_hub_corrected(self, fig, panel_count, ceiling_height, grid_height):
        """Add acoustic treatment panels with proper constraints for The Hub"""
        
        panels_used = 0
        
        # Priority 1: Ceiling panels - ONLY location available, hanging 2" below grid
        ceiling_panel_height = grid_height - (2/12)  # 2" below grid (convert to feet)
        
        # Limited ceiling space - can only fit a few panels without stacking
        ceiling_panels = [
            {"pos": [0, 0, ceiling_panel_height], "name": "Center Ceiling Panel"},
            {"pos": [-2, 1, ceiling_panel_height], "name": "NW Area Ceiling Panel"},
            {"pos": [2, -1, ceiling_panel_height], "name": "East Area Ceiling Panel"},
        ]
        
        ceiling_count = min(len(ceiling_panels), panel_count)
        for i in range(ceiling_count):
            pos_data = ceiling_panels[i]
            self._create_rectangular_panel(
                fig, pos_data['pos'], 2.0, 4.0, 5.5,
                self.colors['absorption_panel'], pos_data['name'],
                "Ceiling panel - hanging 2\" below grid", 'horizontal'
            )
        panels_used += ceiling_count
        
        # Priority 2: Corner bass traps - straddling corners like Studio 8, hanging vertically
        if panel_count > panels_used:
            # Only corners that are NOT on-camera (avoid SW corner area)
            # Based on cardinal labels: N=right, E=bottom, S=left, W=top
            corner_traps = [
                # Northeast corner - where North (right) meets East (bottom)
                {"pos": [4.0, -2.5, 5], "name": "NE Corner Bass Trap", "corner_type": "NE"},
                # Northwest corner - where North (right) meets West (top)
                {"pos": [3.5, 4.0, 5], "name": "NW Corner Bass Trap", "corner_type": "NW"},
            ]
            
            corner_count = min(len(corner_traps), panel_count - panels_used)
            for i in range(corner_count):
                trap = corner_traps[i]
                # Vertical corner bass traps 
                if trap['corner_type'] == 'NW':
                    # NW trap rotated 90deg to be flush with wall
                    self._create_rectangular_panel(
                        fig, trap['pos'], 2.0, 4.0, 5.5,
                        self.colors['bass_trap'], trap['name'],
                        "Corner bass trap - flush with wall", 'corner-135deg'
                    )
                else:
                    # NE trap brought inside space
                    self._create_rectangular_panel(
                        fig, trap['pos'], 2.0, 4.0, 5.5,
                        self.colors['bass_trap'], trap['name'],
                        "Corner bass trap - inside space", 'corner-45deg'
                    )
            panels_used += corner_count
        
        # Priority 3: Wall panels - AVOID SW corner (on-camera), only remaining walls
        # Ensure panels stay within room boundaries
        # Based on cardinal labels: N=right, E=bottom, S=left, W=top
        if panel_count > panels_used:
            wall_panels = [
                # East wall panels - on the EAST wall (bottom in coordinate system, negative Y)
                {"pos": [0, -3.5, 3], "name": "East Wall Panel 1", "orientation": "east-wall"},
                {"pos": [0, -3.5, 6], "name": "East Wall Panel 2", "orientation": "east-wall"},
                
                # North wall panel - on the NORTH wall (right in coordinate system, positive X)
                {"pos": [4.5, 0, 4], "name": "North Wall Panel 1", "orientation": "north-wall"},
            ]
            
            available_wall_panels = min(len(wall_panels), panel_count - panels_used)
            for i in range(available_wall_panels):
                pos_data = wall_panels[i]
                orientation = pos_data['orientation']
                
                # Make panels parallel to their respective walls 
                if orientation == "east-wall":
                    # East wall panels - on east wall (bottom in coordinate system)
                    self._create_rectangular_panel(
                        fig, pos_data['pos'], 4.0, 2.0, 3.0,
                        self.colors['absorption_panel'], pos_data['name'],
                        "East wall panel", 'vertical-short-wall'
                    )
                elif orientation == "north-wall":
                    # North wall panel - on north wall (right in coordinate system)
                    self._create_rectangular_panel(
                        fig, pos_data['pos'], 2.0, 4.0, 3.0,
                        self.colors['absorption_panel'], pos_data['name'],
                        "North wall panel", 'vertical-long-wall'
                    )
            panels_used += available_wall_panels
    
    def _add_hub_furniture_accurate(self, fig, width):
        """Add Hub furniture based on actual PDF floorplan"""
        
        # Set Build area (purple in floorplan) - positioned on left side as shown in PDF
        # More accurate positioning based on floorplan
        set_build_x = [-6, -3, -3, -6, -6]  # Left side, more accurate to PDF
        set_build_y = [-0.5, -0.5, 2.5, 2.5, -0.5]  # Centered vertically in that area
        set_build_z = [0] * 5
        
        fig.add_trace(go.Scatter3d(
            x=set_build_x, y=set_build_y, z=set_build_z,
            mode='lines',
            line=dict(color='#8B008B', width=8),  # Purple for set build
            name='Set Build Area',
            showlegend=True
        ))
        
        # Set build platform/desk at 3.5 feet height
        platform_height = 3.5
        platform_z = [platform_height] * 5
        
        fig.add_trace(go.Scatter3d(
            x=set_build_x, y=set_build_y, z=platform_z,
            mode='lines',
            line=dict(color='#8B008B', width=6),
            name='Set Build Platform',
            showlegend=False
        ))
        
        # Connect floor to platform with vertical supports
        for i in range(4):  # Skip the closing point
            fig.add_trace(go.Scatter3d(
                x=[set_build_x[i], set_build_x[i]], 
                y=[set_build_y[i], set_build_y[i]], 
                z=[0, platform_height],
                mode='lines',
                line=dict(color='#8B008B', width=4),
                showlegend=False
            ))
        
        # Add carpet areas indication (floor level visualization)
        # Rosco Red carpet area
        red_carpet_x = [-1, 5, 5, -1, -1]
        red_carpet_y = [-2, -2, 1, 1, -2]
        red_carpet_z = [0.1] * 5  # Slightly above floor
        
        fig.add_trace(go.Scatter3d(
            x=red_carpet_x, y=red_carpet_y, z=red_carpet_z,
            mode='lines',
            line=dict(color='#DC143C', width=4),  # Crimson red
            name='Rosco Red Carpet',
            showlegend=True
        ))
    
    def _add_room_structure(self, fig, width_EW, length_NS, height):
        """Add room wireframe structure"""
        
        # Floor outline
        floor_x = [0, width_EW, width_EW, 0, 0]
        floor_y = [0, 0, length_NS, length_NS, 0]
        floor_z = [0, 0, 0, 0, 0]
        
        fig.add_trace(go.Scatter3d(
            x=floor_x, y=floor_y, z=floor_z,
            mode='lines',
            line=dict(color=self.colors['room_structure'], width=6),
            name='Floor Outline',
            showlegend=False
        ))
        
        # Ceiling outline
        ceiling_z = [height] * 5
        fig.add_trace(go.Scatter3d(
            x=floor_x, y=floor_y, z=ceiling_z,
            mode='lines',
            line=dict(color=self.colors['room_structure'], width=6),
            name='Ceiling Outline',
            showlegend=False
        ))
        
        # Vertical edges
        corners = [(0,0), (width_EW,0), (width_EW,length_NS), (0,length_NS)]
        for x, y in corners:
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[y, y], z=[0, height],
                mode='lines',
                line=dict(color=self.colors['room_structure'], width=4),
                showlegend=False
            ))
    
    def _add_hallway(self, fig, room_width_EW, room_length_NS, height):
        """Add hallway along the W wall - 6' wide, full height, with NW corner opening"""
        
        hallway_width = 6  # 6 feet wide
        hallway_end_x = 0  # Ends at the W wall
        hallway_start_x = hallway_end_x - hallway_width
        
        # Opening in NW corner - 6' wide opening starting from north wall
        opening_width = 6
        opening_start_y = room_length_NS - opening_width
        
        # Hallway floor (translucent)
        floor_x = [hallway_start_x, hallway_end_x, hallway_end_x, hallway_start_x, hallway_start_x]
        floor_y = [0, 0, room_length_NS, room_length_NS, 0]
        floor_z = [0, 0, 0, 0, 0]
        
        fig.add_trace(go.Scatter3d(
            x=floor_x, y=floor_y, z=floor_z,
            mode='lines',
            line=dict(color=self.colors['hallway'], width=4),
            name='Hallway Floor',
            showlegend=False
        ))
        
        # Hallway ceiling
        ceiling_z = [height] * 5
        fig.add_trace(go.Scatter3d(
            x=floor_x, y=floor_y, z=ceiling_z,
            mode='lines',
            line=dict(color=self.colors['hallway'], width=4),
            name='Hallway Ceiling',
            showlegend=False
        ))
        
        # Vertical edges of hallway
        hallway_corners = [(hallway_start_x, 0), (hallway_end_x, 0), 
                          (hallway_end_x, room_length_NS), (hallway_start_x, room_length_NS)]
        for x, y in hallway_corners:
            # Skip the NW corner opening area
            if not (x == hallway_end_x and y >= opening_start_y):
                fig.add_trace(go.Scatter3d(
                    x=[x, x], y=[y, y], z=[0, height],
                    mode='lines',
                    line=dict(color=self.colors['hallway'], width=3),
                    showlegend=False
                ))
        
        # Hallway walls (translucent surfaces)
        # East wall of hallway (studio side) - with opening in NW corner
        if opening_start_y > 0:
            # Wall section south of opening
            fig.add_trace(go.Mesh3d(
                x=[hallway_end_x, hallway_end_x, hallway_end_x, hallway_end_x],
                y=[0, opening_start_y, opening_start_y, 0],
                z=[0, 0, height, height],
                i=[0, 0], j=[1, 2], k=[2, 3],
                opacity=0.4,
                color=self.colors['hallway'],
                name='Hallway Wall (S)',
                showlegend=False,
                hovertext="Hallway - not part of build"
            ))
        
        # West wall of hallway (exterior)
        fig.add_trace(go.Mesh3d(
            x=[hallway_start_x, hallway_start_x, hallway_start_x, hallway_start_x],
            y=[0, room_length_NS, room_length_NS, 0],
            z=[0, 0, height, height],
            i=[0, 0], j=[1, 2], k=[2, 3],
            opacity=0.4,
            color=self.colors['hallway'],
            name='Hallway Exterior Wall',
            showlegend=False,
            hovertext="Hallway - not part of build"
        ))
        
        # North wall of hallway
        fig.add_trace(go.Mesh3d(
            x=[hallway_start_x, hallway_end_x, hallway_end_x, hallway_start_x],
            y=[room_length_NS, room_length_NS, room_length_NS, room_length_NS],
            z=[0, 0, height, height],
            i=[0, 0], j=[1, 2], k=[2, 3],
            opacity=0.4,
            color=self.colors['hallway'],
            name='Hallway North Wall',
            showlegend=False,
            hovertext="Hallway - not part of build"
        ))
        
        # South wall of hallway
        fig.add_trace(go.Mesh3d(
            x=[hallway_start_x, hallway_end_x, hallway_end_x, hallway_start_x],
            y=[0, 0, 0, 0],
            z=[0, 0, height, height],
            i=[0, 0], j=[1, 2], k=[2, 3],
            opacity=0.4,
            color=self.colors['hallway'],
            name='Hallway South Wall',
            showlegend=False,
            hovertext="Hallway - not part of build"
        ))
        
        # Add legend entry for hallway
        fig.add_trace(go.Scatter3d(
            x=[hallway_start_x + hallway_width/2], 
            y=[room_length_NS/2], 
            z=[height/2],
            mode='markers',
            marker=dict(size=0.1, color=self.colors['hallway']),
            name='Hallway (Not Build)',
            showlegend=True,
            hovertext="6' wide hallway - not part of build, for rendering realism"
        ))
    
    def _add_lighting_grid(self, fig, width_EW, length_NS, grid_height):
        """Add lighting grid plane"""
        
        # Create grid mesh
        x_grid = np.linspace(0, width_EW, 10)
        y_grid = np.linspace(0, length_NS, 8)
        X, Y = np.meshgrid(x_grid, y_grid)
        Z = np.full_like(X, grid_height)
        
        fig.add_trace(go.Surface(
            x=X, y=Y, z=Z,
            colorscale='greys',
            opacity=0.3,
            name='Lighting Grid',
            showscale=False
        ))
        
        # Zone A (below grid)
        fig.add_trace(go.Mesh3d(
            x=[0, width_EW, width_EW, 0],
            y=[0, 0, length_NS, length_NS],
            z=[0, 0, 0, 0],
            i=[0, 0], j=[1, 2], k=[2, 3],
            opacity=0.1,
            color=self.colors['zone_a'],
            name='Zone A (Set Volume)',
            hovertext="Zone A: Below lighting grid - talent and camera area"
        ))
    
    def _add_measurement_positions(self, fig, positions):
        """Add measurement position markers"""
        
        for pos_name, pos_data in positions.items():
            x, y, z = pos_data['coords']
            
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers+text',
                marker=dict(
                    size=pos_data['size'],
                    color=pos_data['color'],
                    symbol='circle',
                    line=dict(width=2, color='white')
                ),
                text=[pos_name],
                textposition="top center",
                name=pos_name,
                hovertemplate=f"<b>{pos_name}</b><br>" +
                             f"Position: ({x:.1f}', {y:.1f}', {z:.1f}')<br>" +
                             "<extra></extra>"
            ))
    
    def _add_treatment_panels_studio8(self, fig, panel_count, room_width_EW, room_length_NS, height, grid_height):
        """Add acoustic treatment panels based on optimal placement from CBC diagram"""
        
        panels_used = 0
        
        # Priority 1: Ceiling Corner Bass Traps - 11" thick for superior bass control
        # 2' down from concrete ceiling (height=14), so at z=12, positioned to cut corners at 45°
        corner_traps = [
            {"pos": [2, 2, height - 2], "name": "SW Corner Bass Trap", "thickness": 11.0, "orientation": "corner-135deg"},
            {"pos": [room_width_EW-2, 2, height - 2], "name": "SE Corner Bass Trap", "thickness": 11.0, "orientation": "corner-45deg"},
            {"pos": [room_width_EW-2, room_length_NS-2, height - 2], "name": "NE Corner Bass Trap", "thickness": 11.0, "orientation": "corner-135deg"},
            {"pos": [2, room_length_NS-2, height - 2], "name": "NW Corner Bass Trap", "thickness": 11.0, "orientation": "corner-45deg"}
        ]
        
        for i, trap in enumerate(corner_traps[:min(4, panel_count)]):
            # Use special color for 11" bass traps to distinguish them
            bass_trap_color = '#b8860b' if trap['thickness'] == 11.0 else self.colors['bass_trap']  # Dark golden rod for 11"
            self._create_rectangular_panel(
                fig, trap['pos'], 4.0, 2.0, trap['thickness'],  # 4' wide, 2' tall, 11" thick
                bass_trap_color, trap['name'],
                f"11\" Corner bass trap - Maximum low-frequency control", trap['orientation']
            )
        panels_used = min(4, panel_count)
        
        # Priority 2: High Midpoint Panels (5.5") - Red in diagram  
        # Above grid, between corners for even coverage (exclude south - too close to monitor wall)
        if panel_count > 4:
            high_midpoint = [
                {"pos": [room_width_EW/2, room_length_NS-2.5, grid_height + 2], "name": "North High Midpoint", "orientation": "rotated"},  # Short wall - rotated 90deg
                {"pos": [1.5, room_length_NS/2, grid_height + 2], "name": "West High Midpoint", "orientation": "horizontal"},  # Long wall
                {"pos": [room_width_EW-1.5, room_length_NS/2, grid_height + 2], "name": "East High Midpoint", "orientation": "horizontal"}  # Long wall
            ]
            
            midpoint_panels = min(3, panel_count - panels_used)
            for i in range(midpoint_panels):
                pos_data = high_midpoint[i]
                orientation = pos_data.get('orientation', 'horizontal')
                # Swap width/length for rotated panels
                if orientation == 'rotated':
                    panel_width, panel_length = 4.0, 2.0  # Rotated: 4' long, 2' wide
                else:
                    panel_width, panel_length = 2.0, 4.0  # Normal: 2' wide, 4' long
                    
                self._create_rectangular_panel(
                    fig, pos_data['pos'], panel_width, panel_length, 5.5,
                    self.colors['absorption_panel'], pos_data['name'],
                    "High midpoint panel - Broadband absorption", 'horizontal'
                )
            panels_used += midpoint_panels
        
        # Priority 3: Ceiling Centre Panels (5.5") - Tan/brown in diagram
        # Acoustically optimized placement: target modal control + first reflections, avoid over-symmetry
        if panel_count > 8:
            # Calculate desk position for acoustic targeting
            desk_center_x = room_width_EW/2
            desk_center_y = (room_length_NS/2) - 5
            
            ceiling_center = [
                # Primary: Above critical listening area (desk region)
                {"pos": [desk_center_x, desk_center_y + 2, grid_height + 1.5], "name": "Primary Desk Ceiling"},
                {"pos": [desk_center_x - 3, desk_center_y, grid_height + 1.5], "name": "Host C Ceiling"},
                {"pos": [desk_center_x + 3, desk_center_y, grid_height + 1.5], "name": "Host A Ceiling"},
                
                # Secondary: Break up length-wise modes (27.42' creates 20.4Hz fundamental)
                {"pos": [room_width_EW/2, room_length_NS * 0.25, grid_height + 1.5], "name": "South Modal Break", "orientation": "horizontal"},
                {"pos": [room_width_EW/2, (room_length_NS * 0.75) - 1, grid_height + 1.5], "name": "North Modal Break", "orientation": "rotated"},
                
                # Tertiary: Asymmetric placement to avoid creating new patterns
                {"pos": [room_width_EW * 0.3, room_length_NS * 0.4, grid_height + 1.5], "name": "SW Asymmetric"},
                {"pos": [room_width_EW * 0.7, room_length_NS * 0.6, grid_height + 1.5], "name": "NE Asymmetric"},
                {"pos": [room_width_EW * 0.25, room_length_NS * 0.65, grid_height + 1.5], "name": "NW Offset"},
                {"pos": [room_width_EW * 0.75, room_length_NS * 0.35, grid_height + 1.5], "name": "SE Offset"}
            ]
            
            ceiling_panels = min(9, panel_count - panels_used)
            for i in range(ceiling_panels):
                pos_data = ceiling_center[i]
                orientation = pos_data.get('orientation', 'horizontal')
                # Swap width/length for rotated panels
                if orientation == 'rotated':
                    panel_width, panel_length = 4.0, 2.0  # Rotated: 4' long, 2' wide
                else:
                    panel_width, panel_length = 2.0, 4.0  # Normal: 2' wide, 4' long
                    
                self._create_rectangular_panel(
                    fig, pos_data['pos'], panel_width, panel_length, 5.5,
                    self.colors['absorption_panel'], pos_data['name'],
                    "Ceiling center panel - RT60 control", 'horizontal'
                )
            panels_used += ceiling_panels
        
        # Priority 4: North Wall Panels (3") - Gold in diagram
        # ONLY on North wall (Zone A) - easy and effective placement, always use 4 panels
        if panel_count > 17:
            north_wall = [
                {"pos": [room_width_EW/5, room_length_NS-0.25, 6], "name": "North Wall Panel 1"},  # North wall at high y
                {"pos": [2*room_width_EW/5, room_length_NS-0.25, 6], "name": "North Wall Panel 2"},  
                {"pos": [3*room_width_EW/5, room_length_NS-0.25, 6], "name": "North Wall Panel 3"},
                {"pos": [4*room_width_EW/5, room_length_NS-0.25, 6], "name": "North Wall Panel 4"}
            ]
            
            north_panels = min(4, panel_count - panels_used)
            for i in range(north_panels):
                pos_data = north_wall[i]
                self._create_rectangular_panel(
                    fig, pos_data['pos'], 2.0, 4.0, 3.0,  # 3" thick for wall panels
                    self.colors['absorption_panel'], pos_data['name'],
                    "North wall panel - First reflection control", 'vertical-short-wall'
                )
            panels_used += north_panels
        
        # Priority 4B: E Wall Panel in NE Corner (3") - Immediately downstream of N wall panels
        # Single panel on E wall of NE corner to eliminate bare surface
        if panel_count > 21:
            e_wall_panel = {"pos": [room_width_EW-0.25, room_length_NS-3, 6], "name": "NE Corner E Wall Panel"}
            
            if panel_count - panels_used >= 1:
                self._create_rectangular_panel(
                    fig, e_wall_panel['pos'], 2.0, 4.0, 3.0,  # 3" thick for wall panels
                    self.colors['absorption_panel'], e_wall_panel['name'],
                    "E wall panel - NE corner coverage", 'vertical-long-wall'
                )
                panels_used += 1
        
        # Priority 5: Grid Clouds (3") - Green in diagram  
        # Below lighting grid, above talent positions - positioned like CBC diagram
        if panel_count > 22:
            # Calculate desk position (matches main method)
            desk_center_x = room_width_EW/2
            desk_center_y = (room_length_NS/2) - 5
            
            # Position clouds based on actual host positions from CBC diagram
            # Host A (Reference): SE corner of desk
            # Host C (Talent): SW corner of desk  
            # Center position: Above desk center
            grid_clouds = [
                {"pos": [desk_center_x + 4, desk_center_y - 1, grid_height - 0.5], "name": "Host A Grid Cloud"},    # Above Host A position
                {"pos": [desk_center_x, desk_center_y, grid_height - 0.5], "name": "Host B Grid Cloud"},  # Above desk center
                {"pos": [desk_center_x - 4, desk_center_y - 1, grid_height - 0.5], "name": "Host C Grid Cloud"}     # Above Host C position
            ]
            
            cloud_panels = min(3, panel_count - panels_used)  
            for i in range(cloud_panels):
                pos_data = grid_clouds[i]
                self._create_rectangular_panel(
                    fig, pos_data['pos'], 2.0, 4.0, 3.0,  # 3" thick for grid clouds
                    '#90EE90', pos_data['name'],  # Light green color
                    "Grid cloud - Talent position treatment", 'horizontal'
                )
            panels_used += cloud_panels
    
    def _create_rectangular_panel(self, fig, position, width, length, thickness, color, name, description, orientation='horizontal', corner_type=None):
        """Create a proper 3D rectangular acoustic panel (2'x4' with actual thickness)"""
        x, y, z = position
        
        # Convert inches to feet for thickness
        thickness_ft = thickness / 12.0  # 3" = 0.25', 5.5" = 0.458'
        
        if orientation == 'horizontal':
            # Panel lying flat (ceiling mount)
            hw, hl = width/2, length/2
            vertices = [
                [x-hw, y-hl, z], [x+hw, y-hl, z], [x+hw, y+hl, z], [x-hw, y+hl, z],  # bottom face
                [x-hw, y-hl, z+thickness_ft], [x+hw, y-hl, z+thickness_ft], [x+hw, y+hl, z+thickness_ft], [x-hw, y+hl, z+thickness_ft]  # top face
            ]
        elif orientation == 'corner-45deg':
            # Panel mounted at 45° angle straddling corner, PERPENDICULAR to floor
            import numpy as np
            hw, hl = width/2, length/2  # width=4', length=2' (height when vertical)
            # Rotate panel 45 degrees around z-axis, but keep it vertical (perpendicular to floor)
            cos45, sin45 = np.cos(np.pi/4), np.sin(np.pi/4)
            
            # Define panel corners - vertical orientation (perpendicular to floor)
            local_coords = [
                [-hw, -thickness_ft/2, -hl], [hw, -thickness_ft/2, -hl], [hw, thickness_ft/2, -hl], [-hw, thickness_ft/2, -hl],  # bottom edge
                [-hw, -thickness_ft/2, hl], [hw, -thickness_ft/2, hl], [hw, thickness_ft/2, hl], [-hw, thickness_ft/2, hl]  # top edge
            ]
            
            vertices = []
            for lx, ly, lz in local_coords:
                # Rotate by 45° around z-axis and translate to position
                rx = lx * cos45 - ly * sin45 + x
                ry = lx * sin45 + ly * cos45 + y
                rz = lz + z
                vertices.append([rx, ry, rz])
        elif orientation == 'corner-135deg':
            # Panel mounted at 135° angle (rotated 90° from 45°), PERPENDICULAR to floor
            import numpy as np
            hw, hl = width/2, length/2  # width=4', length=2' (height when vertical)
            # Rotate panel 135 degrees around z-axis, but keep it vertical (perpendicular to floor)
            cos135, sin135 = np.cos(3*np.pi/4), np.sin(3*np.pi/4)
            
            # Define panel corners - vertical orientation (perpendicular to floor)
            local_coords = [
                [-hw, -thickness_ft/2, -hl], [hw, -thickness_ft/2, -hl], [hw, thickness_ft/2, -hl], [-hw, thickness_ft/2, -hl],  # bottom edge
                [-hw, -thickness_ft/2, hl], [hw, -thickness_ft/2, hl], [hw, thickness_ft/2, hl], [-hw, thickness_ft/2, hl]  # top edge
            ]
            
            vertices = []
            for lx, ly, lz in local_coords:
                # Rotate by 135° around z-axis and translate to position
                rx = lx * cos135 - ly * sin135 + x
                ry = lx * sin135 + ly * cos135 + y
                rz = lz + z
                vertices.append([rx, ry, rz])
        elif orientation == 'corner-45deg-tilted':
            # Panel tilted 45° inward - top stays in place, bottom moves toward corner
            import numpy as np
            hw, hl = width/2, length/2  # width=4', length=2' (height when vertical)
            thickness_ft = thickness / 12.0
            
            # Calculate tilt: keep top edge in place, move bottom edge toward corner
            tilt_offset = hl * np.sin(np.pi/4)  # How much to move bottom edge toward corner
            
            # Rotate panel 45° around z-axis for corner orientation
            cos45, sin45 = np.cos(np.pi/4), np.sin(np.pi/4)
            
            # Define tilted panel corners - lower z (floor side) closer to corner, higher z (ceiling side) toward center
            local_coords = [
                # Lower edge (z = -hl, closer to floor) - move toward corner
                [-hw, -thickness_ft/2, -hl], [hw, -thickness_ft/2, -hl], [hw, thickness_ft/2, -hl], [-hw, thickness_ft/2, -hl],
                # Upper edge (z = hl, closer to ceiling) - move toward room center
                [-hw, -thickness_ft/2, hl], [hw, -thickness_ft/2, hl], [hw, thickness_ft/2, hl], [-hw, thickness_ft/2, hl]
            ]
            
            vertices = []
            for i, (lx, ly, lz) in enumerate(local_coords):
                # Apply tilt based on corner type - bottom toward corner, top toward center
                if corner_type == "SE":
                    # SE corner: toward [+x, -y]
                    corner_dir_x, corner_dir_y = 1, -1
                elif corner_type == "NW":
                    # NW corner: toward [-x, +y] - REVERSED
                    corner_dir_x, corner_dir_y = 1, -1
                else:
                    # Default for debugging
                    corner_dir_x, corner_dir_y = 1, 1
                
                if i < 4:  # Lower vertices (z = -hl) - move toward corner
                    tilt_x = tilt_offset * corner_dir_x * cos45
                    tilt_y = tilt_offset * corner_dir_y * sin45
                else:  # Upper vertices (z = hl) - move toward room center
                    tilt_x = -tilt_offset * corner_dir_x * cos45
                    tilt_y = -tilt_offset * corner_dir_y * sin45
                
                # Rotate by 45° around z-axis and translate to position
                rx = (lx + tilt_x) * cos45 - (ly + tilt_y) * sin45 + x
                ry = (lx + tilt_x) * sin45 + (ly + tilt_y) * cos45 + y
                rz = lz + z
                vertices.append([rx, ry, rz])
        elif orientation == 'corner-135deg-tilted':
            # Panel tilted 45° inward - top stays in place, bottom moves toward corner
            import numpy as np
            hw, hl = width/2, length/2  # width=4', length=2' (height when vertical)
            thickness_ft = thickness / 12.0
            
            # Calculate tilt: keep top edge in place, move bottom edge toward corner
            tilt_offset = hl * np.sin(np.pi/4)  # How much to move bottom edge toward corner
            
            # Rotate panel 135° around z-axis for corner orientation
            cos135, sin135 = np.cos(3*np.pi/4), np.sin(3*np.pi/4)
            
            # Define tilted panel corners - lower z (floor side) closer to corner, higher z (ceiling side) toward center
            local_coords = [
                # Lower edge (z = -hl, closer to floor) - move toward corner
                [-hw, -thickness_ft/2, -hl], [hw, -thickness_ft/2, -hl], [hw, thickness_ft/2, -hl], [-hw, thickness_ft/2, -hl],
                # Upper edge (z = hl, closer to ceiling) - move toward room center
                [-hw, -thickness_ft/2, hl], [hw, -thickness_ft/2, hl], [hw, thickness_ft/2, hl], [-hw, thickness_ft/2, hl]
            ]
            
            vertices = []
            for i, (lx, ly, lz) in enumerate(local_coords):
                # Apply tilt based on corner type - bottom toward corner, top toward center
                if corner_type == "SW":
                    # SW corner: toward [-x, -y]
                    corner_dir_x, corner_dir_y = -1, -1
                elif corner_type == "NE":
                    # NE corner: toward [+x, +y] - REVERSED
                    corner_dir_x, corner_dir_y = -1, -1
                else:
                    # Default for debugging
                    corner_dir_x, corner_dir_y = 1, 1
                
                if i < 4:  # Lower vertices (z = -hl) - move toward corner
                    tilt_x = tilt_offset * corner_dir_x * cos135
                    tilt_y = tilt_offset * corner_dir_y * sin135
                else:  # Upper vertices (z = hl) - move toward room center
                    tilt_x = -tilt_offset * corner_dir_x * cos135
                    tilt_y = -tilt_offset * corner_dir_y * sin135
                
                # Rotate by 135° around z-axis and translate to position
                rx = (lx + tilt_x) * cos135 - (ly + tilt_y) * sin135 + x
                ry = (lx + tilt_x) * sin135 + (ly + tilt_y) * cos135 + y
                rz = lz + z
                vertices.append([rx, ry, rz])
        elif orientation == 'vertical-long-wall':
            # Panel mounted vertically on long wall (East/West)
            hw, hl = width/2, length/2
            vertices = [
                [x, y-hw, z-hl], [x, y+hw, z-hl], [x, y+hw, z+hl], [x, y-hw, z+hl],  # back face
                [x+thickness_ft, y-hw, z-hl], [x+thickness_ft, y+hw, z-hl], [x+thickness_ft, y+hw, z+hl], [x+thickness_ft, y-hw, z+hl]  # front face
            ]
        else:  # vertical-short-wall (North/South)
            # Panel mounted on short wall (North/South)
            hw, hl = width/2, length/2
            vertices = [
                [x-hw, y, z-hl], [x+hw, y, z-hl], [x+hw, y, z+hl], [x-hw, y, z+hl],  # back face
                [x-hw, y+thickness_ft, z-hl], [x+hw, y+thickness_ft, z-hl], [x+hw, y+thickness_ft, z+hl], [x-hw, y+thickness_ft, z+hl]  # front face
            ]
        
        # Extract coordinates
        x_coords = [v[0] for v in vertices]
        y_coords = [v[1] for v in vertices]
        z_coords = [v[2] for v in vertices]
        
        # Use simpler approach - create multiple rectangular faces
        # Bottom face (z=z)
        fig.add_trace(go.Mesh3d(
            x=x_coords[:4], y=y_coords[:4], z=z_coords[:4],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=color, opacity=0.8, showlegend=False,
            hovertext=f"{name}<br>{description}<br>2'×4' Roxul Panel<br>{thickness}\" thick"
        ))
        
        # Top face (z=z+thickness)  
        fig.add_trace(go.Mesh3d(
            x=x_coords[4:8], y=y_coords[4:8], z=z_coords[4:8],
            i=[0, 0], j=[1, 2], k=[2, 3],
            color=color, opacity=0.8, showlegend=False,
            hovertext=f"{name}<br>{description}<br>2'×4' Roxul Panel<br>{thickness}\" thick"
        ))
        
        # Side faces (connect bottom to top)
        for i in range(4):
            next_i = (i + 1) % 4
            side_x = [x_coords[i], x_coords[next_i], x_coords[next_i+4], x_coords[i+4]]
            side_y = [y_coords[i], y_coords[next_i], y_coords[next_i+4], y_coords[i+4]]
            side_z = [z_coords[i], z_coords[next_i], z_coords[next_i+4], z_coords[i+4]]
            
            fig.add_trace(go.Mesh3d(
                x=side_x, y=side_y, z=side_z,
                i=[0, 0], j=[1, 2], k=[2, 3],
                color=color, opacity=0.8, showlegend=False,
                hovertext=f"{name}<br>{description}<br>2'×4' Roxul Panel<br>{thickness}\" thick"
            ))
        
        # Add a single legend entry
        fig.add_trace(go.Scatter3d(
            x=[x_coords[0]], y=[y_coords[0]], z=[z_coords[0]],
            mode='markers', marker=dict(size=0.1, color=color),
            name=name, showlegend=True,
            hovertext=f"{name}<br>{description}<br>2'×4' Roxul Panel<br>{thickness}\" thick"
        ))

    def _add_corner_bass_trap(self, fig, position, name):
        """Add corner bass trap as proper 2'x4' panel"""
        self._create_rectangular_panel(
            fig, position, 2.0, 4.0, 5.5,  # 2'x4' x 5.5" thick
            self.colors['bass_trap'], name,
            "Corner bass trap - Low frequency control",
            'horizontal'
        )
    
    def _add_ceiling_panel(self, fig, position, name):
        """Add ceiling-mounted absorption panel as proper 2'x4' panel"""
        self._create_rectangular_panel(
            fig, position, 2.0, 4.0, 5.5,  # 2'x4' x 5.5" thick
            self.colors['absorption_panel'], name,
            "Ceiling panel - Broadband absorption",
            'horizontal'
        )
    
    def _add_wall_panel(self, fig, position, name):
        """Add wall-mounted absorption panel as proper 2'x4' panel"""
        # Determine wall orientation based on position
        x, y, z = position
        room_width_EW = 23.375  # Room width (East-West direction) - short walls  
        room_length_NS = 27.42  # Room length (North-South direction) - long walls
        
        if x < 1:  # West wall (long wall)
            orientation = 'vertical-long-wall'
        elif x > room_width_EW - 1:  # East wall (long wall)
            orientation = 'vertical-long-wall'
        else:  # North or South wall (short walls)
            orientation = 'vertical-short-wall'
            
        self._create_rectangular_panel(
            fig, position, 2.0, 4.0, 5.5,  # 2'x4' x 5.5" thick
            self.colors['absorption_panel'], name,
            "Wall panel - First reflection control",
            orientation
        )
    
    def _add_studio8_furniture(self, fig, room_width_EW=23.375, room_length_NS=27.42):
        """Add key furniture and equipment"""
        
        # Plexiglass desk - rotated 90° and moved 5' toward south wall
        desk_length = 5   # Slightly larger: now 5' in N-S direction
        desk_width = 10   # Slightly larger: now 10' in E-W direction  
        desk_height = 3.5   # Split the difference: now 3.5' high
        desk_x = room_width_EW/2 - desk_width/2   # Still centered E-W
        desk_y = (room_length_NS/2 - desk_length/2) - 5  # Moved 5' toward south wall
        
        # Create oval desk using parametric equations
        import numpy as np
        
        # Oval parameters
        center_x = desk_x + desk_width/2
        center_y = desk_y + desk_length/2
        a = desk_width/2  # Semi-major axis (4' radius in E-W direction)
        b = desk_length/2  # Semi-minor axis (2' radius in N-S direction)
        
        # Generate oval points with higher resolution for smoother appearance
        theta = np.linspace(0, 2*np.pi, 64)
        oval_x = center_x + a * np.cos(theta)
        oval_y = center_y + b * np.sin(theta)
        
        # Desk surface with better materials and lighting
        desk_color = 'rgba(173, 216, 230, 0.75)'  # Light blue with slightly more opacity
        
        # Bottom surface of oval desk
        fig.add_trace(go.Mesh3d(
            x=oval_x,
            y=oval_y,
            z=np.zeros_like(oval_x),
            opacity=0.75,
            color=desk_color,
            name='Oval Plexiglass Desk',
            showlegend=True,
            alphahull=0,
            lighting=dict(ambient=0.3, diffuse=0.8, specular=0.5, roughness=0.1, fresnel=0.2),
            lightposition=dict(x=100, y=200, z=300)
        ))
        
        # Top surface of oval desk with glossy finish - made mostly opaque
        fig.add_trace(go.Mesh3d(
            x=oval_x,
            y=oval_y,
            z=np.full_like(oval_x, desk_height),
            opacity=0.95,
            color=desk_color,
            showlegend=False,
            alphahull=0,
            lighting=dict(ambient=0.2, diffuse=0.9, specular=0.8, roughness=0.05, fresnel=0.3),
            lightposition=dict(x=100, y=200, z=300)
        ))
        
        # Improved side surface with better segmentation
        n_segments = len(oval_x)
        for i in range(0, n_segments, 2):  # Skip every other segment for cleaner look
            next_i = (i + 2) % n_segments
            fig.add_trace(go.Mesh3d(
                x=[oval_x[i], oval_x[next_i], oval_x[next_i], oval_x[i]],
                y=[oval_y[i], oval_y[next_i], oval_y[next_i], oval_y[i]],
                z=[0, 0, desk_height, desk_height],
                i=[0, 0], j=[1, 2], k=[2, 3],
                opacity=0.65,
                color=desk_color,
                showlegend=False,
                lighting=dict(ambient=0.4, diffuse=0.7, specular=0.4, roughness=0.2),
                lightposition=dict(x=100, y=200, z=300)
            ))
    
    def _add_human_figures(self, fig, positions):
        """Add simple low-res human figures for Host A and Host C"""
        import numpy as np
        
        # Get host positions
        host_a_pos = positions["Host A (Reference)"]["coords"]
        host_c_pos = positions["Host C (Talent)"]["coords"]
        
        # Create lifelike news reporter avatars (standing, facing north)
        for host_name, pos, avatar_config in [
            ("Host A", host_a_pos, {
                'suit_color': '#2c3e50',      # Dark navy suit
                'shirt_color': '#ecf0f1',     # White shirt
                'tie_color': '#c0392b',       # Red tie
                'skin_color': '#deb887',      # Light skin tone
                'hair_color': '#8b4513'       # Brown hair
            }),
            ("Host C", host_c_pos, {
                'suit_color': '#34495e',      # Charcoal suit
                'shirt_color': '#e8f4fd',     # Light blue shirt
                'tie_color': '#2980b9',       # Blue tie
                'skin_color': '#cd853f',      # Medium skin tone
                'hair_color': '#2c2c2c'       # Dark hair
            })
        ]:
            x, y, z = pos
            
            # Professional news reporter avatar - lifelike proportions
            # Total height ~5.8' (professional broadcast standard)
            body_height = 2.0
            body_base_z = 3.5  # Standing behind desk
            head_size = 0.3
            
            # Hair (styled for TV)
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[body_base_z + body_height + head_size + 0.1],
                mode='markers',
                marker=dict(size=8, color=avatar_config['hair_color'], symbol='circle', opacity=0.8),
                name=f'{host_name} Hair',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Hair Style"
            ))
            
            # Head with skin tone
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[body_base_z + body_height + head_size],
                mode='markers',
                marker=dict(size=7, color=avatar_config['skin_color'], symbol='circle', opacity=0.95),
                name=f'{host_name} Head',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Head"
            ))
            
            # Eyes (small markers for detail)
            eye_z = body_base_z + body_height + head_size
            fig.add_trace(go.Scatter3d(
                x=[x-0.05, x+0.05], y=[y+0.1, y+0.1], z=[eye_z, eye_z],
                mode='markers',
                marker=dict(size=3, color='black', symbol='circle'),
                name=f'{host_name} Eyes',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Eyes"
            ))
            
            # Neck with skin tone
            neck_z = body_base_z + body_height
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[y, y], z=[neck_z, neck_z + head_size/2],
                mode='lines',
                line=dict(color=avatar_config['skin_color'], width=6),
                name=f'{host_name} Neck',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Neck"
            ))
            
            # Suit jacket (professional attire)
            jacket_top = body_base_z + body_height * 0.85
            jacket_bottom = body_base_z + body_height * 0.2
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[y, y], z=[jacket_bottom, jacket_top],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=12),
                name=f'{host_name} Suit Jacket',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Suit Jacket"
            ))
            
            # Dress shirt (visible at collar)
            shirt_top = body_base_z + body_height * 0.95
            shirt_collar = neck_z - 0.05
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[y, y], z=[shirt_top, shirt_collar],
                mode='lines',
                line=dict(color=avatar_config['shirt_color'], width=8),
                name=f'{host_name} Dress Shirt',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Dress Shirt"
            ))
            
            # Tie (professional accessory)
            tie_top = body_base_z + body_height * 0.9
            tie_bottom = body_base_z + body_height * 0.4
            fig.add_trace(go.Scatter3d(
                x=[x, x], y=[y, y], z=[tie_top, tie_bottom],
                mode='lines',
                line=dict(color=avatar_config['tie_color'], width=4),
                name=f'{host_name} Tie',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Tie"
            ))
            
            # Professional suit jacket shoulders
            shoulder_z = body_base_z + body_height * 0.85
            shoulder_width = 1.2  # Broader for professional look
            fig.add_trace(go.Scatter3d(
                x=[x-shoulder_width, x+shoulder_width], y=[y, y], z=[shoulder_z, shoulder_z],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=8),
                name=f'{host_name} Suit Shoulders',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Suit Shoulders"
            ))
            
            # Professional arms in suit sleeves
            elbow_z = body_base_z + body_height * 0.6
            hand_z = body_base_z + body_height * 0.3
            
            # Left arm with suit sleeve
            fig.add_trace(go.Scatter3d(
                x=[x-shoulder_width, x-0.8, x-0.6], 
                y=[y, y-0.1, y-0.2], 
                z=[shoulder_z, elbow_z, hand_z],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=6),
                name=f'{host_name} Left Arm Suit',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Left Arm in Suit"
            ))
            
            # Left hand (skin tone)
            fig.add_trace(go.Scatter3d(
                x=[x-0.6], y=[y-0.2], z=[hand_z],
                mode='markers',
                marker=dict(size=4, color=avatar_config['skin_color'], symbol='circle'),
                name=f'{host_name} Left Hand',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Left Hand"
            ))
            
            # Right arm with suit sleeve
            fig.add_trace(go.Scatter3d(
                x=[x+shoulder_width, x+0.8, x+0.6], 
                y=[y, y-0.1, y-0.2], 
                z=[shoulder_z, elbow_z, hand_z],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=6),
                name=f'{host_name} Right Arm Suit',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Right Arm in Suit"
            ))
            
            # Right hand (skin tone)
            fig.add_trace(go.Scatter3d(
                x=[x+0.6], y=[y-0.2], z=[hand_z],
                mode='markers',
                marker=dict(size=4, color=avatar_config['skin_color'], symbol='circle'),
                name=f'{host_name} Right Hand',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Right Hand"
            ))
            
            # Professional suit pants
            pelvis_z = body_base_z + body_height * 0.2
            knee_z = body_base_z + body_height * 0.1
            feet_z = 0
            
            # Left leg in suit pants
            fig.add_trace(go.Scatter3d(
                x=[x-0.2, x-0.25, x-0.3], 
                y=[y, y-0.2, y-0.3], 
                z=[pelvis_z, knee_z, feet_z],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=7),
                name=f'{host_name} Left Leg Suit',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Left Leg in Suit Pants"
            ))
            
            # Right leg in suit pants
            fig.add_trace(go.Scatter3d(
                x=[x+0.2, x+0.25, x+0.3], 
                y=[y, y-0.2, y-0.3], 
                z=[pelvis_z, knee_z, feet_z],
                mode='lines',
                line=dict(color=avatar_config['suit_color'], width=7),
                name=f'{host_name} Right Leg Suit',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Right Leg in Suit Pants"
            ))
            
            # Professional dress shoes
            fig.add_trace(go.Scatter3d(
                x=[x-0.3, x+0.3], y=[y-0.3, y-0.3], z=[feet_z, feet_z],
                mode='markers',
                marker=dict(size=6, color='#1a1a1a', symbol='square'),
                name=f'{host_name} Dress Shoes',
                legendgroup=f'{host_name}',
                showlegend=False,
                hovertext=f"{host_name} - Professional Dress Shoes"
            ))
            
            # Add a single legend entry for the complete news reporter avatar
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[body_base_z + body_height/2],
                mode='markers',
                marker=dict(size=0.1, color=avatar_config['suit_color']),
                name=f'{host_name} News Reporter',
                legendgroup=f'{host_name}',
                showlegend=True,
                visible='legendonly',
                hovertext=f"{host_name} - Professional News Reporter Avatar"
            ))

def create_panel_placement_guide():
    """Create detailed panel placement visualization"""
    
    visualizer = Enhanced3DVisualizer()
    
    # Create models with different panel counts
    panel_scenarios = [
        {"count": 12, "title": "Minimum Treatment (Drape Compensation)"},
        {"count": 25, "title": "Recommended Treatment"},
        {"count": 40, "title": "Maximum Budget Treatment"}
    ]
    
    models = {}
    for scenario in panel_scenarios:
        models[scenario["title"]] = visualizer.create_studio8_detailed_model(
            show_panels=True, 
            panel_count=scenario["count"]
        )
    
    return models

if __name__ == "__main__":
    # Test the enhanced visualizer with modal analysis
    visualizer = Enhanced3DVisualizer()
    fig = visualizer.create_studio8_with_modal_analysis(show_panels=True, panel_count=25, show_zone_a=True, show_zone_b=True)
    fig.show()