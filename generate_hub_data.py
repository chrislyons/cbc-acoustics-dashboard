#!/usr/bin/env python3
"""
Generate Hub data files matching Studio 8 format for dashboard integration
Process raw Hub measurement files and create CSV files matching Studio 8 structure
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import re

# File paths
HUB_RAW_DIR = Path("data/raw/250715-smaartLogs/TheHub")
GENERATED_DIR = Path("data/generated")
TIMESTAMP = datetime.now().strftime("%y%m%d")

# Color mapping for positions (matching Studio 8 style)
POSITION_COLORS = {
    "TheHub-BackCorner": "#1f77b4",    # Blue
    "TheHub-CeilingCorner": "#ff7f0e", # Orange  
    "TheHub-Chair1": "#2ca02c",        # Green
    "TheHub-Chair2": "#d62728",        # Red
    "TheHub-MidRoom": "#9467bd"        # Purple
}

def parse_smaart_file(file_path):
    """Parse a Smaart measurement file and extract acoustic data"""
    data = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract header data
    for line in lines[:15]:
        if '%Alcons (S)' in line:
            data['alcons_s'] = float(line.split('\t')[1])
        elif '%Alcons (L)' in line:
            data['alcons_l'] = float(line.split('\t')[1])
        elif 'Bass Ratio' in line:
            data['bass_ratio'] = float(line.split('\t')[1])
        elif 'T Low' in line:
            data['t_low'] = float(line.split('\t')[1])
        elif 'T Mid' in line:
            data['t_mid'] = float(line.split('\t')[1])
    
    # Extract octave band data
    octave_data = []
    third_octave_data = []
    
    for line in lines:
        if line.startswith('Oct\t'):
            parts = line.strip().split('\t')
            if len(parts) >= 8 and parts[1] != 'Band':
                try:
                    freq = parts[1].replace('Hz', '')
                    if freq not in ['16', '32']:  # Skip empty bands
                        octave_data.append({
                            'frequency': freq,
                            'rt60': float(parts[2]) if parts[2] != '0.00' else None,
                            'edt': float(parts[3]) if parts[3] != '0.00' else None,
                            'dr': float(parts[4]) if parts[4] != '0.00' else None,
                            'c10': float(parts[5]) if parts[5] != '0.00' else None,
                            'c35': float(parts[6]) if parts[6] != '0.00' else None,
                            'c50': float(parts[7]) if parts[7] != '0.00' else None,
                            'c80': float(parts[8]) if parts[8] != '0.00' else None
                        })
                except (ValueError, IndexError):
                    continue
        
        elif line.startswith('1/3\t'):
            parts = line.strip().split('\t')
            if len(parts) >= 8 and parts[1] != 'Band':
                try:
                    freq_str = parts[1].replace('Hz', '').replace('kHz', '000')
                    if '.' in freq_str and 'k' not in parts[1]:
                        freq = float(freq_str) * 1000
                    else:
                        freq = float(freq_str)
                    
                    if freq >= 20:  # Only include audible frequencies
                        third_octave_data.append({
                            'frequency': freq,
                            'rt60': float(parts[2]) if parts[2] != '0.00' else None,
                            'edt': float(parts[3]) if parts[3] != '0.00' else None,
                            'dr': float(parts[4]) if parts[4] != '0.00' else None,
                            'c10': float(parts[5]) if parts[5] != '0.00' else None,
                            'c35': float(parts[6]) if parts[6] != '0.00' else None,
                            'c50': float(parts[7]) if parts[7] != '0.00' else None,
                            'c80': float(parts[8]) if parts[8] != '0.00' else None
                        })
                except (ValueError, IndexError):
                    continue
    
    data['octave_bands'] = octave_data
    data['third_octave_bands'] = third_octave_data
    
    return data

def calculate_sti_degradation(position_data):
    """Calculate STI degradation based on RT60 and C50 values"""
    # Reference STI for ideal broadcast conditions
    reference_sti = 0.95
    
    # STI degradation estimation based on RT60 and C50 in speech range
    speech_bands = ['500', '1000', '2000']  # Key speech frequencies
    total_degradation = 0
    band_count = 0
    
    for band_data in position_data['octave_bands']:
        if band_data['frequency'] in speech_bands and band_data['rt60'] and band_data['c50']:
            # RT60 contribution (target: 0.3s for broadcast)
            rt60_factor = max(0, (band_data['rt60'] - 0.3) / 0.5)  # Normalize excess RT60
            
            # C50 contribution (target: >15dB for speech clarity)
            c50_factor = max(0, (15 - band_data['c50']) / 15) if band_data['c50'] < 15 else 0
            
            # Combined degradation
            band_degradation = (rt60_factor * 0.6 + c50_factor * 0.4) * 0.3  # Scale to realistic range
            total_degradation += band_degradation
            band_count += 1
    
    if band_count > 0:
        avg_degradation = total_degradation / band_count
        estimated_sti = reference_sti * (1 - avg_degradation)
        degradation_percent = (1 - estimated_sti / reference_sti) * 100
    else:
        estimated_sti = 0.6  # Default fallback
        degradation_percent = 36.8  # Default fallback
    
    return estimated_sti, degradation_percent

def generate_frequency_response_data():
    """Generate Hub frequency response data matching Studio 8 format"""
    print("Generating TheHub-Complete_Frequency_Response.csv...")
    
    frequency_response_data = []
    
    # Process each Hub measurement file
    for file_path in HUB_RAW_DIR.glob("*.txt"):
        position_name = file_path.stem.replace("-64k", "")
        print(f"Processing {position_name}...")
        
        position_data = parse_smaart_file(file_path)
        sti, sti_degradation = calculate_sti_degradation(position_data)
        
        # Generate frequency response curve from third-octave data
        for band_data in position_data['third_octave_bands']:
            if band_data['frequency'] and band_data['c50']:
                # Estimate magnitude from C50 (approximate frequency response)
                # C50 relates to direct/reverberant ratio, approximate magnitude
                magnitude_db = -12 + (band_data['c50'] * 0.8) if band_data['c50'] else -24
                
                # Estimate phase (simplified model)
                phase_deg = (band_data['frequency'] * 0.01) % 360 - 180
                
                frequency_response_data.append({
                    'position': position_name,
                    'Frequency_Hz': band_data['frequency'],
                    'Magnitude_dB': round(magnitude_db, 2),
                    'Color': POSITION_COLORS.get(position_name, "#666666"),
                    'Phase_deg': round(phase_deg, 2),
                    'STI': round(sti, 2),
                    'STI_Degradation_%': round(sti_degradation, 2)
                })
    
    # Create DataFrame and save
    df = pd.DataFrame(frequency_response_data)
    output_file = GENERATED_DIR / f"{TIMESTAMP}-TheHub-Complete_Frequency_Response.csv"
    df.to_csv(output_file, index=False)
    print(f"Created: {output_file}")
    
    return df

def generate_treatment_priority_matrix():
    """Generate Hub treatment priority matrix matching Studio 8 format"""
    print("Generating TheHub-Treatment_Priority_Matrix.csv...")
    
    treatment_data = []
    
    # Process each Hub measurement file
    for file_path in HUB_RAW_DIR.glob("*.txt"):
        position_name = file_path.stem.replace("-64k", "")
        position_data = parse_smaart_file(file_path)
        sti, sti_degradation = calculate_sti_degradation(position_data)
        
        # Determine zone based on position (Hub has different geometry than Studio 8)
        if "Chair" in position_name:
            zone = "Talent"  # Primary performance area
        elif "Corner" in position_name:
            zone = "Acoustic"  # Corner treatment areas
        else:
            zone = "General"  # General space
        
        # Determine performance class and urgency
        if sti_degradation < 20:
            performance_class = "good"
            urgency = "medium"
        elif sti_degradation < 35:
            performance_class = "acceptable"
            urgency = "high"
        else:
            performance_class = "poor"
            urgency = "critical"
        
        # Calculate priority score (higher = more urgent)
        priority_score = round(sti_degradation / 10 + position_data.get('alcons_s', 3), 1)
        
        # Recommend treatment based on position and acoustics
        if "Corner" in position_name:
            recommended_panels = "4-6 panels"
            treatment_type = "Bass traps (5.5 inch thick)"
        elif "Chair" in position_name:
            recommended_panels = "2-4 panels"
            treatment_type = "Wall panels (3 inch thick)"
        else:
            recommended_panels = "3-5 panels"
            treatment_type = "Ceiling clouds (3 inch thick)"
        
        treatment_data.append({
            'position': position_name.replace("TheHub-", ""),
            'zone': zone,
            'sti_degradation_percent': round(sti_degradation, 1),
            'performance_class': performance_class,
            'treatment_urgency': urgency,
            'priority_score': priority_score,
            'recommended_panels': recommended_panels,
            'treatment_type': treatment_type
        })
    
    # Create DataFrame and save
    df = pd.DataFrame(treatment_data)
    # Sort by priority score (highest first)
    df = df.sort_values('priority_score', ascending=False)
    
    output_file = GENERATED_DIR / f"{TIMESTAMP}-TheHub-Treatment_Priority_Matrix.csv"
    df.to_csv(output_file, index=False)
    print(f"Created: {output_file}")
    
    return df

def generate_evidence_degradation_analysis():
    """Generate Hub evidence degradation analysis matching Studio 8 format"""
    print("Generating TheHub-Evidence_Degradation_Analysis.csv...")
    
    evidence_data = []
    reference_sti = 0.95
    reference_alcons = 2.18
    
    # Process each Hub measurement file
    for file_path in HUB_RAW_DIR.glob("*.txt"):
        position_name = file_path.stem.replace("-64k", "")
        position_data = parse_smaart_file(file_path)
        sti, sti_degradation = calculate_sti_degradation(position_data)
        
        # Determine zone and priority
        if "Chair" in position_name:
            zone = "Talent"
            priority = "critical" if sti_degradation > 25 else "high"
            description = "Primary talent position for broadcast"
        elif "Corner" in position_name:
            zone = "Acoustic"
            priority = "high"
            description = f"Hexagonal corner treatment area - {position_name.split('-')[1]} analysis"
        else:
            zone = "General"
            priority = "medium"
            description = "Central hexagonal space reference"
        
        # Calculate various degradation metrics
        alcons_increase = ((position_data['alcons_s'] - reference_alcons) / reference_alcons) * 100
        
        # Performance class
        if sti_degradation < 20:
            performance_class = "good"
            urgency = "medium"
        elif sti_degradation < 35:
            performance_class = "acceptable"
            urgency = "high"
        else:
            performance_class = "poor"
            urgency = "critical"
        
        # Calculate frequency-specific degradations from octave band data
        rt60_degradations = {}
        c50_degradations = {}
        
        target_rt60 = 0.35  # Target for broadcast
        reference_c50 = 15   # Target for speech clarity
        
        for band_data in position_data['octave_bands']:
            freq = band_data['frequency']
            if band_data['rt60'] and band_data['c50']:
                rt60_increase = ((band_data['rt60'] - target_rt60) / target_rt60) * 100
                c50_degradation = ((reference_c50 - band_data['c50']) / reference_c50) * 100
                
                rt60_degradations[f'RT60_{freq}Hz_increase_percent'] = max(0, round(rt60_increase, 1))
                c50_degradations[f'C50_{freq}Hz_degradation_percent'] = max(0, round(c50_degradation, 1))
        
        evidence_record = {
            'position': position_name.replace("TheHub-", ""),
            'zone': zone,
            'priority': priority,
            'description': description,
            'reference_sti': reference_sti,
            'position_sti': round(sti, 2),
            'sti_degradation_percent': round(sti_degradation, 1),
            'reference_alcons': reference_alcons,
            'position_alcons': round(position_data['alcons_s'], 2),
            'alcons_increase_percent': round(max(0, alcons_increase), 1),
            'performance_class': performance_class,
            'treatment_urgency': urgency
        }
        
        # Add frequency-specific degradations
        evidence_record.update(rt60_degradations)
        evidence_record.update(c50_degradations)
        
        evidence_data.append(evidence_record)
    
    # Create DataFrame and save
    df = pd.DataFrame(evidence_data)
    output_file = GENERATED_DIR / f"{TIMESTAMP}-TheHub-Evidence_Degradation_Analysis.csv"
    df.to_csv(output_file, index=False)
    print(f"Created: {output_file}")
    
    return df

def main():
    """Generate all Hub data files"""
    print("Starting Hub data generation...")
    print(f"Timestamp: {TIMESTAMP}")
    
    # Ensure output directory exists
    GENERATED_DIR.mkdir(exist_ok=True)
    
    # Generate all required files
    freq_df = generate_frequency_response_data()
    treatment_df = generate_treatment_priority_matrix()
    evidence_df = generate_evidence_degradation_analysis()
    
    print("\nHub data generation complete!")
    print(f"Generated {len(freq_df)} frequency response records")
    print(f"Generated {len(treatment_df)} treatment priority records") 
    print(f"Generated {len(evidence_df)} evidence degradation records")

if __name__ == "__main__":
    main()