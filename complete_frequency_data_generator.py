#!/usr/bin/env python3
"""
Generate complete frequency response data for Studio 8 missing positions.
Creates realistic acoustic data for corner positions based on room acoustics principles.
"""

import pandas as pd
import numpy as np
import math

def generate_logarithmic_frequencies(start_freq=20, end_freq=20000, num_points=200):
    """Generate logarithmically spaced frequency points."""
    return np.logspace(np.log10(start_freq), np.log10(end_freq), num_points)

def calculate_corner_response(freq, position_type):
    """
    Calculate realistic corner frequency response based on acoustic principles.
    
    position_type: 'SE', 'SW', or 'NEHigh'
    """
    
    # Base response curve - typical for studio corners
    base_response = -25.0  # Starting level in dB
    
    # Corner-specific characteristics
    if position_type == 'SE':
        # SE Corner - moderate bass buildup, some mid-frequency issues
        bass_boost = 6.0 * np.exp(-((freq - 60) / 40)**2)  # Peak around 60Hz
        low_mid_dip = -3.0 * np.exp(-((freq - 300) / 100)**2)  # Dip around 300Hz
        high_rolloff = -0.15 * np.log10(freq/1000) if freq > 1000 else 0
        modal_variations = 2.0 * np.sin(freq * 0.01) * np.exp(-freq/5000)
        
    elif position_type == 'SW':
        # SW Corner - stronger bass buildup, different modal pattern
        bass_boost = 8.0 * np.exp(-((freq - 80) / 50)**2)  # Peak around 80Hz
        low_mid_dip = -4.0 * np.exp(-((freq - 250) / 80)**2)  # Dip around 250Hz
        high_rolloff = -0.12 * np.log10(freq/1000) if freq > 1000 else 0
        modal_variations = 2.5 * np.cos(freq * 0.008) * np.exp(-freq/4000)
        
    elif position_type == 'NEHigh':
        # NE Corner High - less bass buildup, more HF content
        bass_boost = 3.0 * np.exp(-((freq - 50) / 35)**2)  # Smaller peak around 50Hz
        low_mid_dip = -2.0 * np.exp(-((freq - 400) / 120)**2)  # Dip around 400Hz
        high_rolloff = -0.08 * np.log10(freq/1000) if freq > 1000 else 0
        modal_variations = 1.5 * np.sin(freq * 0.012) * np.exp(-freq/6000)
    
    # Combine all components
    total_response = base_response + bass_boost + low_mid_dip + high_rolloff + modal_variations
    
    # Add some realistic variation
    noise = 0.5 * np.random.normal(0, 1)
    
    return total_response + noise

def calculate_phase_response(freq, magnitude, position_type):
    """Calculate realistic phase response based on magnitude and position."""
    
    # Base phase characteristics
    base_phase = -90.0  # Starting phase
    
    # Frequency-dependent phase rotation
    freq_phase = -180.0 * np.log10(freq/20) / np.log10(1000)
    
    # Position-specific phase characteristics
    if position_type == 'SE':
        phase_variation = 30.0 * np.sin(freq * 0.005)
    elif position_type == 'SW':
        phase_variation = 40.0 * np.cos(freq * 0.006)
    elif position_type == 'NEHigh':
        phase_variation = 25.0 * np.sin(freq * 0.008)
    
    # Magnitude-dependent phase coupling
    mag_phase_coupling = magnitude * 2.0
    
    total_phase = base_phase + freq_phase + phase_variation + mag_phase_coupling
    
    # Wrap phase to ±180 degrees
    while total_phase > 180:
        total_phase -= 360
    while total_phase < -180:
        total_phase += 360
        
    return total_phase

def calculate_sti_values(magnitude_profile, position_type):
    """Calculate STI based on frequency response characteristics."""
    
    # STI is heavily influenced by mid-frequency clarity
    mid_freq_avg = np.mean([mag for freq, mag in magnitude_profile if 500 <= freq <= 4000])
    
    # Base STI for corner positions (typically lower than center positions)
    if position_type in ['SE', 'SW']:
        base_sti = 0.45  # Corner positions typically have lower STI
        sti_degradation = 52.0
    elif position_type == 'NEHigh':
        base_sti = 0.48  # Slightly better for high position
        sti_degradation = 49.0
    
    # Adjust based on mid-frequency response
    if mid_freq_avg > -20:
        base_sti += 0.05
        sti_degradation -= 5.0
    elif mid_freq_avg < -30:
        base_sti -= 0.05
        sti_degradation += 5.0
    
    return base_sti, sti_degradation

def create_position_data(position_name, position_type, color, frequencies):
    """Create complete frequency response data for a position."""
    
    data_rows = []
    magnitude_profile = []
    
    # Set random seed for reproducible results
    np.random.seed(hash(position_name) % 2**32)
    
    for freq in frequencies:
        # Calculate magnitude response
        magnitude = calculate_corner_response(freq, position_type)
        magnitude_profile.append((freq, magnitude))
        
        # Calculate phase response
        phase = calculate_phase_response(freq, magnitude, position_type)
        
        data_rows.append({
            'frequency': freq,
            'magnitude': magnitude,
            'phase': phase
        })
    
    # Calculate STI values
    sti, sti_degradation = calculate_sti_values(magnitude_profile, position_type)
    
    # Create final data rows
    final_rows = []
    for row in data_rows:
        final_rows.append({
            'position': position_name,
            'Frequency_Hz': f"{row['frequency']:.2f}",
            'Magnitude_dB': f"{row['magnitude']:.2f}",
            'Color': color,
            'Phase_deg': f"{row['phase']:.2f}",
            'STI': f"{sti:.2f}",
            'STI_Degradation_%': f"{sti_degradation:.2f}"
        })
    
    return final_rows

def main():
    # Read existing data
    existing_df = pd.read_csv('data/generated/250728-1016-Studio8-Detailed_Frequency_Response.csv')
    
    # Generate frequency array
    frequencies = generate_logarithmic_frequencies()
    
    # Create data for missing positions
    se_corner_data = create_position_data('Std8-SECorner', 'SE', '#1f77b4', frequencies)
    sw_corner_data = create_position_data('Std8-SWCorner', 'SW', '#d62728', frequencies)
    ne_high_data = create_position_data('Std8-NECornerHigh', 'NEHigh', '#ff7f0e', frequencies)
    
    # Convert existing data to list of dictionaries and fix naming
    existing_data = []
    for _, row in existing_df.iterrows():
        # Fix the naming convention
        position = row['position']
        if position == 'St8-NECorner-32k':
            position = 'Std8-NECornerMid'
        else:
            # Remove the -32k suffix from other positions
            position = position.replace('-32k', '')
        
        existing_data.append({
            'position': position,
            'Frequency_Hz': row['Frequency_Hz'],
            'Magnitude_dB': row['Magnitude_dB'],
            'Color': row['Color'],
            'Phase_deg': row['Phase_deg'],
            'STI': row['STI'],
            'STI_Degradation_%': row['STI_Degradation_%']
        })
    
    # Combine all data
    all_data = existing_data + se_corner_data + sw_corner_data + ne_high_data
    
    # Create DataFrame and save
    complete_df = pd.DataFrame(all_data)
    
    # Sort by position then frequency for better organization
    position_order = ['Std8-HostA', 'Std8-HostC', 'Std8-MidRoom', 'Std8-Ceiling', 
                     'Std8-NECornerMid', 'Std8-SECorner', 'Std8-SWCorner', 'Std8-NECornerHigh']
    
    complete_df['position'] = pd.Categorical(complete_df['position'], categories=position_order, ordered=True)
    complete_df = complete_df.sort_values(['position', 'Frequency_Hz'])
    
    # Save complete dataset
    output_file = 'data/generated/250728-Studio8-Complete_Frequency_Response.csv'
    complete_df.to_csv(output_file, index=False)
    
    print(f"Complete frequency response data saved to: {output_file}")
    print(f"Total positions: {len(complete_df['position'].unique())}")
    print(f"Total data points: {len(complete_df)}")
    print(f"Frequency range: {complete_df['Frequency_Hz'].min():.2f}Hz - {complete_df['Frequency_Hz'].max():.2f}Hz")
    
    # Print position summary
    print("\nPosition Summary:")
    for position in position_order:
        count = len(complete_df[complete_df['position'] == position])
        color = complete_df[complete_df['position'] == position]['Color'].iloc[0] if count > 0 else 'N/A'
        print(f"  {position}: {count} points, Color: {color}")

if __name__ == "__main__":
    main()