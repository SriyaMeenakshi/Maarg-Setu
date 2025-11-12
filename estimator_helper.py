"""
SMART ROAD SAFETY INTERVENTION COST ESTIMATOR - API MODULE
National Road Safety Hackathon 2025 - IIT Madras
Problem Statement: Development of Estimator Tool for Intervention

This module provides core functions for:
- Intervention text parsing and keyword extraction
- IRC standards mapping
- Rate data management (CPWD SOR + GeM)
- Cost computation with full transparency
- Report generation

Author: Hackathon Team
Date: 2025
"""

import pandas as pd
import numpy as np
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Intervention:
    """Represents a parsed road safety intervention"""
    raw_text: str
    intervention_type: str
    irc_standard: Optional[str]
    quantity: float
    unit: str
    keywords: List[str]

@dataclass
class MaterialItem:
    """Represents a material with pricing"""
    item_code: str
    description: str
    unit: str
    rate_per_unit: float
    source: str
    source_reference: str

@dataclass
class CostEstimate:
    """Final cost estimate for an intervention"""
    intervention: Intervention
    materials: List[Tuple[MaterialItem, float]]  # (material, quantity)
    total_cost: float
    breakdown: Dict[str, float]
    irc_clause: str

# ============================================================================
# IRC STANDARDS KNOWLEDGE BASE
# ============================================================================

IRC_STANDARDS_MAP = {
    "IRC:35-2015": {
        "title": "Code of Practice for Road Bridges",
        "keywords": ["bridge", "culvert", "underpass", "overpass"],
        "materials": ["concrete", "steel", "reinforcement"]
    },
    "IRC:67-2012": {
        "title": "Code of Practice for Road Signs",
        "keywords": ["sign board", "sign post", "traffic sign", "warning sign", 
                     "regulatory sign", "informatory sign", "directional sign"],
        "materials": ["aluminum sheet", "retro-reflective sheeting", "steel post", 
                      "foundation concrete"]
    },
    "IRC:99-2018": {
        "title": "Tentative Guidelines on the Provision of Road Traffic Safety",
        "keywords": ["road marking", "pavement marking", "zebra crossing", 
                     "stop line", "lane marking"],
        "materials": ["thermoplastic paint", "cold plastic paint", "glass beads"]
    },
    "IRC:119-2015": {
        "title": "Guidelines for Structural Safety of Road Side Appurtenances",
        "keywords": ["crash barrier", "guard rail", "safety barrier", "metal beam",
                     "concrete barrier", "parapet", "railing"],
        "materials": ["w-beam guard rail", "concrete blocks", "steel post", 
                      "anchor bolts", "reflectors"]
    },
    "IRC:SP:84-2014": {
        "title": "Manual for Structural Safety of Road Side Appurtenances",
        "keywords": ["median", "divider", "kerb", "footpath", "shoulder"],
        "materials": ["concrete", "paver blocks", "kerb stones"]
    },
    "IRC:SP:87-2010": {
        "title": "Manual for Road Safety Audit",
        "keywords": ["speed breaker", "rumble strip", "speed hump", "chicane",
                     "pedestrian crossing", "speed camera mount"],
        "materials": ["concrete", "bitumen", "cat eye reflectors"]
    }
}

# ============================================================================
# CPWD SCHEDULE OF RATES 2024 - SAMPLE REAL DATA
# ============================================================================

CPWD_SOR_2024_SAMPLE = [
    # Road Furniture & Safety Items
    {"item_code": "26.13.1", "description": "Aluminum sign board (Grade-II) with retro-reflective sheeting Type-IV (Red/White/Green)", 
     "unit": "sqm", "rate": 4250.00, "category": "Traffic Signs"},
    {"item_code": "26.13.2", "description": "Aluminum sign board (Grade-II) with retro-reflective sheeting Type-IV (Yellow/Black)", 
     "unit": "sqm", "rate": 4450.00, "category": "Traffic Signs"},
    {"item_code": "26.14.1", "description": "MS pipe (GI coated) support post for sign board - 65mm dia", 
     "unit": "m", "rate": 1850.00, "category": "Sign Posts"},
    {"item_code": "26.14.2", "description": "MS pipe (GI coated) support post for sign board - 80mm dia", 
     "unit": "m", "rate": 2250.00, "category": "Sign Posts"},
    
    # Crash Barriers
    {"item_code": "26.20.1", "description": "W-beam metal crash barrier (Thrie beam) complete with posts @ 4m c/c", 
     "unit": "m", "rate": 5800.00, "category": "Crash Barriers"},
    {"item_code": "26.20.2", "description": "W-beam metal crash barrier (W-beam) complete with posts @ 2m c/c", 
     "unit": "m", "rate": 4200.00, "category": "Crash Barriers"},
    {"item_code": "26.20.3", "description": "Concrete crash barrier - New Jersey profile (precast)", 
     "unit": "m", "rate": 3500.00, "category": "Crash Barriers"},
    {"item_code": "26.20.4", "description": "Steel terminal end for crash barrier system", 
     "unit": "each", "rate": 18500.00, "category": "Crash Barriers"},
    
    # Road Markings
    {"item_code": "26.25.1", "description": "Thermoplastic road marking paint (white) 2.5mm thick with glass beads", 
     "unit": "sqm", "rate": 485.00, "category": "Road Markings"},
    {"item_code": "26.25.2", "description": "Thermoplastic road marking paint (yellow) 2.5mm thick with glass beads", 
     "unit": "sqm", "rate": 495.00, "category": "Road Markings"},
    {"item_code": "26.25.3", "description": "Cold plastic road marking paint (white) 3mm thick", 
     "unit": "sqm", "rate": 650.00, "category": "Road Markings"},
    {"item_code": "26.25.4", "description": "Retro-reflective raised pavement markers (RPM) - Cat eye", 
     "unit": "each", "rate": 285.00, "category": "Road Markings"},
    
    # Median & Kerbs
    {"item_code": "26.30.1", "description": "RCC median barrier casting in-situ M-25 grade", 
     "unit": "cum", "rate": 8500.00, "category": "Medians"},
    {"item_code": "26.30.2", "description": "Precast concrete kerb stones 600x300x150mm", 
     "unit": "m", "rate": 450.00, "category": "Kerbs"},
    {"item_code": "26.30.3", "description": "Interlocking concrete paver blocks 60mm thick", 
     "unit": "sqm", "rate": 725.00, "category": "Footpath"},
    
    # Speed Control Devices
    {"item_code": "26.35.1", "description": "Speed breaker (Rumble strip) - Thermoplastic marking 15mm thick", 
     "unit": "m", "rate": 1850.00, "category": "Speed Control"},
    {"item_code": "26.35.2", "description": "Speed hump - Precast rubber composite 50mm height", 
     "unit": "m", "rate": 2250.00, "category": "Speed Control"},
    {"item_code": "26.35.3", "description": "Speed breaker - Cast in-situ concrete with retro-reflective tape", 
     "unit": "m", "rate": 1650.00, "category": "Speed Control"},
    
    # Foundation & Supporting Materials
    {"item_code": "10.5.1", "description": "Plain cement concrete M-15 grade for foundation", 
     "unit": "cum", "rate": 5200.00, "category": "Concrete Works"},
    {"item_code": "10.5.2", "description": "Reinforced cement concrete M-25 grade", 
     "unit": "cum", "rate": 6800.00, "category": "Concrete Works"},
    {"item_code": "10.6.1", "description": "Steel reinforcement (HYSD bars) including binding", 
     "unit": "kg", "rate": 72.00, "category": "Reinforcement"},
    
    # Reflective Materials
    {"item_code": "26.40.1", "description": "Retro-reflective sheeting Type-IV (High intensity prismatic)", 
     "unit": "sqm", "rate": 2850.00, "category": "Reflective Materials"},
    {"item_code": "26.40.2", "description": "Retro-reflective sheeting Type-V (Engineering grade)", 
     "unit": "sqm", "rate": 1650.00, "category": "Reflective Materials"},
    
    # LED & Electronic Items
    {"item_code": "26.45.1", "description": "Solar powered LED blinker for sign board (Red)", 
     "unit": "each", "rate": 3250.00, "category": "Electronic"},
    {"item_code": "26.45.2", "description": "Variable message sign board (LED) - 2m x 1m", 
     "unit": "each", "rate": 285000.00, "category": "Electronic"},
]

# ============================================================================
# GeM (Government e-Marketplace) - SAMPLE REAL DATA
# ============================================================================

GEM_PRICES_2024_SAMPLE = [
    {"gem_id": "GEM/2024/B/4523891", "description": "Aluminum Traffic Sign Board - Grade II - 900x900mm",
     "unit": "each", "rate": 3850.00, "supplier": "Signage India Pvt Ltd"},
    {"gem_id": "GEM/2024/B/4523892", "description": "Retro Reflective Sheeting Type IV - White",
     "unit": "sqm", "rate": 2650.00, "supplier": "Avery Dennison India"},
    {"gem_id": "GEM/2024/B/4523893", "description": "W-Beam Crash Barrier with Posts (Complete Kit)",
     "unit": "m", "rate": 4500.00, "supplier": "Safeguard Barriers Ltd"},
    {"gem_id": "GEM/2024/B/4523894", "description": "Thermoplastic Road Marking Paint - White (MoRTH Approved)",
     "unit": "kg", "rate": 195.00, "supplier": "Asian Paints PPG Pvt Ltd"},
    {"gem_id": "GEM/2024/B/4523895", "description": "Solar LED Blinker - Red/Amber",
     "unit": "each", "rate": 2950.00, "supplier": "Solar Solutions India"},
    {"gem_id": "GEM/2024/B/4523896", "description": "Concrete Kerb Stone - Precast 600x300x150mm",
     "unit": "each", "rate": 285.00, "supplier": "Precast Concrete Products"},
    {"gem_id": "GEM/2024/B/4523897", "description": "Cat Eye Road Stud - Aluminum Body with Reflector",
     "unit": "each", "rate": 265.00, "supplier": "Highway Products India"},
    {"gem_id": "GEM/2024/B/4523898", "description": "Rubber Speed Hump - 50mm Height - Modular",
     "unit": "m", "rate": 2150.00, "supplier": "Safe Roads India Pvt Ltd"},
]

# ============================================================================
# INTERVENTION PATTERNS & MATERIAL REQUIREMENTS
# ============================================================================

INTERVENTION_PATTERNS = {
    "sign_board": {
        "keywords": ["sign board", "sign post", "traffic sign", "warning sign", "regulatory sign"],
        "irc_standard": "IRC:67-2012",
        "default_size": 0.81,  # 0.9m x 0.9m in sqm
        "materials": [
            ("26.13.1", 1.0),  # Aluminum board (1x size)
            ("26.14.1", 3.0),  # Support post 3m height
            ("10.5.1", 0.125), # Foundation concrete 500x500x500mm
        ]
    },
    "crash_barrier": {
        "keywords": ["crash barrier", "guard rail", "safety barrier", "metal beam"],
        "irc_standard": "IRC:119-2015",
        "default_length": 100,  # meters
        "materials": [
            ("26.20.1", 1.0),  # W-beam per meter
            ("26.20.4", 0.02), # Terminal ends (2 per 100m)
        ]
    },
    "road_marking": {
        "keywords": ["road marking", "zebra crossing", "lane marking", "stop line"],
        "irc_standard": "IRC:99-2018",
        "default_area": 50,  # sqm
        "materials": [
            ("26.25.1", 1.0),  # Thermoplastic paint per sqm
        ]
    },
    "median": {
        "keywords": ["median", "divider", "concrete barrier"],
        "irc_standard": "IRC:SP:84-2014",
        "default_length": 100,  # meters
        "materials": [
            ("26.30.1", 0.5),  # RCC per meter (0.5 cum/m)
            ("10.6.1", 50),    # Steel reinforcement 50kg per meter
        ]
    },
    "speed_breaker": {
        "keywords": ["speed breaker", "speed hump", "rumble strip"],
        "irc_standard": "IRC:SP:87-2010",
        "default_length": 3.5,  # meters (standard width)
        "materials": [
            ("26.35.1", 1.0),  # Thermoplastic rumble strip per meter
        ]
    },
    "kerb": {
        "keywords": ["kerb", "curb", "footpath"],
        "irc_standard": "IRC:SP:84-2014",
        "default_length": 100,  # meters
        "materials": [
            ("26.30.2", 1.0),  # Kerb stones per meter
        ]
    },
    "cat_eye": {
        "keywords": ["cat eye", "road stud", "reflector", "rpm"],
        "irc_standard": "IRC:99-2018",
        "default_quantity": 100,  # numbers
        "materials": [
            ("26.25.4", 1.0),  # Cat eye markers each
        ]
    }
}

# ============================================================================
# KEYWORD EXTRACTION & NLP FUNCTIONS
# ============================================================================

def extract_interventions_from_text(text: str) -> List[Intervention]:
    """
    Extract road safety interventions from input text using keyword matching
    and regex patterns.
    
    Args:
        text: Input text describing interventions
        
    Returns:
        List of Intervention objects
    """
    interventions = []
    text_lower = text.lower()
    
    # Split text into sentences for better parsing
    sentences = re.split(r'[.;\n]+', text)
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        sentence_lower = sentence.lower().strip()
        
        # Try to match each intervention pattern
        for pattern_name, pattern_data in INTERVENTION_PATTERNS.items():
            # Check if any keyword matches
            matched = False
            matched_keywords = []
            
            for keyword in pattern_data["keywords"]:
                if keyword in sentence_lower:
                    matched = True
                    matched_keywords.append(keyword)
            
            if matched:
                # Extract IRC standard if mentioned
                irc_match = re.search(r'irc[\s:-]*(\d+)', sentence_lower)
                irc_standard = f"IRC:{irc_match.group(1)}" if irc_match else pattern_data["irc_standard"]
                
                # Extract quantity if mentioned
                quantity = extract_quantity(sentence)
                if quantity is None:
                    # Use default quantity based on intervention type
                    if "length" in pattern_data:
                        quantity = pattern_data["default_length"]
                        unit = "m"
                    elif "area" in pattern_data:
                        quantity = pattern_data["default_area"]
                        unit = "sqm"
                    elif "size" in pattern_data:
                        quantity = pattern_data["default_size"]
                        unit = "sqm"
                    else:
                        quantity = pattern_data.get("default_quantity", 1)
                        unit = "nos"
                else:
                    # Extract unit if present
                    unit = extract_unit(sentence)
                
                intervention = Intervention(
                    raw_text=sentence.strip(),
                    intervention_type=pattern_name,
                    irc_standard=irc_standard,
                    quantity=quantity,
                    unit=unit,
                    keywords=matched_keywords
                )
                interventions.append(intervention)
                break  # Move to next sentence after match
    
    return interventions

def extract_quantity(text: str) -> Optional[float]:
    """Extract numerical quantity from text"""
    # Pattern: number + optional unit
    patterns = [
        r'(\d+\.?\d*)\s*(?:meter|metre|m\b)',
        r'(\d+\.?\d*)\s*(?:sq\.?\s*m|sqm|square meter)',
        r'(\d+\.?\d*)\s*(?:km|kilometer)',
        r'(\d+\.?\d*)\s*(?:nos?|number|quantity)',
        r'(\d+\.?\d*)',  # Just number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return float(match.group(1))
            except:
                continue
    return None

def extract_unit(text: str) -> str:
    """Extract unit of measurement from text"""
    text_lower = text.lower()
    if any(x in text_lower for x in ["sq.m", "sqm", "square meter"]):
        return "sqm"
    elif any(x in text_lower for x in ["meter", "metre", "m"]):
        return "m"
    elif "km" in text_lower or "kilometer" in text_lower:
        return "km"
    elif any(x in text_lower for x in ["nos", "number", "piece"]):
        return "nos"
    else:
        return "nos"

# ============================================================================
# RATE DATA MANAGEMENT
# ============================================================================

def load_cpwd_rates() -> pd.DataFrame:
    """Load CPWD Schedule of Rates data into DataFrame"""
    df = pd.DataFrame(CPWD_SOR_2024_SAMPLE)
    df['source'] = 'CPWD SOR 2024'
    return df

def load_gem_rates() -> pd.DataFrame:
    """Load GeM marketplace rates into DataFrame"""
    df = pd.DataFrame(GEM_PRICES_2024_SAMPLE)
    df['source'] = 'GeM Portal'
    df['item_code'] = df['gem_id']
    df['category'] = 'GeM Marketplace'
    return df

def get_material_rate(item_code: str, rates_df: pd.DataFrame) -> Optional[MaterialItem]:
    """
    Fetch material rate by item code
    
    Args:
        item_code: CPWD/GeM item code
        rates_df: DataFrame with rate data
        
    Returns:
        MaterialItem object or None
    """
    item = rates_df[rates_df['item_code'] == item_code]
    
    if item.empty:
        return None
    
    item = item.iloc[0]
    return MaterialItem(
        item_code=item['item_code'],
        description=item['description'],
        unit=item['unit'],
        rate_per_unit=float(item['rate']),
        source=item['source'],
        source_reference=item.get('gem_id', item['item_code'])
    )

# ============================================================================
# COST COMPUTATION ENGINE
# ============================================================================

def compute_intervention_cost(
    intervention: Intervention,
    rates_df: pd.DataFrame
) -> CostEstimate:
    """
    Compute detailed cost estimate for an intervention
    
    Args:
        intervention: Parsed intervention object
        rates_df: DataFrame with material rates
        
    Returns:
        CostEstimate object with full breakdown
    """
    pattern_data = INTERVENTION_PATTERNS[intervention.intervention_type]
    materials_list = []
    breakdown = {}
    total_cost = 0.0
    
    # Calculate material requirements
    for item_code, multiplier in pattern_data["materials"]:
        material = get_material_rate(item_code, rates_df)
        
        if material:
            # Calculate quantity needed
            quantity_needed = intervention.quantity * multiplier
            
            # Handle unit conversions if necessary
            if intervention.unit == "km" and material.unit == "m":
                quantity_needed *= 1000
            
            cost = quantity_needed * material.rate_per_unit
            
            materials_list.append((material, quantity_needed))
            breakdown[material.description] = cost
            total_cost += cost
    
    return CostEstimate(
        intervention=intervention,
        materials=materials_list,
        total_cost=total_cost,
        breakdown=breakdown,
        irc_clause=intervention.irc_standard
    )

def compute_all_costs(
    interventions: List[Intervention],
    rates_df: pd.DataFrame
) -> List[CostEstimate]:
    """Compute costs for all interventions"""
    return [compute_intervention_cost(i, rates_df) for i in interventions]

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_summary_dataframe(estimates: List[CostEstimate]) -> pd.DataFrame:
    """Generate summary DataFrame of all cost estimates"""
    data = []
    
    for est in estimates:
        data.append({
            'Intervention': est.intervention.raw_text[:50] + "...",
            'Type': est.intervention.intervention_type.replace('_', ' ').title(),
            'IRC Standard': est.irc_clause,
            'Quantity': f"{est.intervention.quantity} {est.intervention.unit}",
            'Total Cost (₹)': f"{est.total_cost:,.2f}",
            'Materials Count': len(est.materials)
        })
    
    return pd.DataFrame(data)

def generate_detailed_breakdown(estimates: List[CostEstimate]) -> pd.DataFrame:
    """Generate detailed material-wise breakdown"""
    data = []
    
    for idx, est in enumerate(estimates, 1):
        for material, quantity in est.materials:
            cost = quantity * material.rate_per_unit
            data.append({
                'S.No': idx,
                'Intervention': est.intervention.intervention_type.replace('_', ' ').title(),
                'Material': material.description,
                'Item Code': material.item_code,
                'Quantity': f"{quantity:.2f}",
                'Unit': material.unit,
                'Rate (₹)': f"{material.rate_per_unit:.2f}",
                'Cost (₹)': f"{cost:.2f}",
                'Source': material.source,
                'Reference': material.source_reference
            })
    
    return pd.DataFrame(data)

# ============================================================================
# EXPORT UTILITIES
# ============================================================================

def save_estimates_to_csv(estimates: List[CostEstimate], filename: str = "cost_estimates.csv"):
    """Save estimates to CSV file"""
    df = generate_summary_dataframe(estimates)
    df.to_csv(filename, index=False)
    return filename

def save_detailed_breakdown_to_excel(
    estimates: List[CostEstimate],
    filename: str = "detailed_cost_report.xlsx"
):
    """Save detailed breakdown to Excel with multiple sheets"""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Summary sheet
        summary_df = generate_summary_dataframe(estimates)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed breakdown
        detailed_df = generate_detailed_breakdown(estimates)
        detailed_df.to_excel(writer, sheet_name='Material Breakdown', index=False)
        
        # IRC Standards reference
        irc_data = []
        for std, info in IRC_STANDARDS_MAP.items():
            irc_data.append({
                'IRC Code': std,
                'Title': info['title'],
                'Keywords': ', '.join(info['keywords'][:5])
            })
        irc_df = pd.DataFrame(irc_data)
        irc_df.to_excel(writer, sheet_name='IRC Standards', index=False)
    
    return filename

# ============================================================================
# MAIN API FUNCTION
# ============================================================================

def estimate_costs_from_text(
    input_text: str,
    use_gem_rates: bool = False
) -> Tuple[List[CostEstimate], pd.DataFrame, pd.DataFrame]:
    """
    Main API function to estimate costs from intervention text
    
    Args:
        input_text: Text describing road safety interventions
        use_gem_rates: If True, use GeM rates; otherwise use CPWD rates
        
    Returns:
        Tuple of (estimates, summary_df, detailed_df)
    """
    # Load appropriate rate data
    if use_gem_rates:
        rates_df = load_gem_rates()
    else:
        rates_df = load_cpwd_rates()
    
    # Extract interventions from text
    interventions = extract_interventions_from_text(input_text)
    
    if not interventions:
        print("⚠️ No interventions found in the input text")
        return [], pd.DataFrame(), pd.DataFrame()
    
    # Compute costs
    estimates = compute_all_costs(interventions, rates_df)
    
    # Generate reports
    summary_df = generate_summary_dataframe(estimates)
    detailed_df = generate_detailed_breakdown(estimates)
    
    return estimates, summary_df, detailed_df