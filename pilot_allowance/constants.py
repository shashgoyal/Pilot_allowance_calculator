"""
Constants and configuration for Pilot Allowance Calculator.
Based on Revised Cockpit Crew Allowances effective 1st January 2026.
"""

# ============================================================================
# ALLOWANCE RATES (Revised effective 1st January 2026)
# ============================================================================

RATES = {
    'tail_swap': {'CP': 1500, 'FO': 750},
    'transit_per_hour': {'CP': 1000, 'FO': 500},
    'layover_base': {'CP': 3000, 'FO': 1500},  # For 10:01 to 24 hours
    'layover_extra_per_hour': {'CP': 150, 'FO': 75},  # Beyond 24 hours
    'deadhead_per_block_hour': {'CP': 4000, 'FO': 2000},
    'night_per_hour': {'CP': 2000, 'FO': 1000},
}

# ============================================================================
# TIMEZONE OFFSETS FROM IST (UTC+5:30)
# Offset in hours: positive means ahead of IST, negative means behind IST
# ============================================================================

AIRPORT_TIMEZONE_OFFSET_FROM_IST = {
    # Middle East
    'RUH': -2.5,   # Riyadh, Saudi Arabia (UTC+3)
    'JED': -2.5,   # Jeddah, Saudi Arabia (UTC+3)
    'DMM': -2.5,   # Dammam, Saudi Arabia (UTC+3)
    'DOH': -2.5,   # Doha, Qatar (UTC+3)
    'BAH': -2.5,   # Bahrain (UTC+3)
    'KWI': -2.5,   # Kuwait (UTC+3)
    'MCT': -1.5,   # Muscat, Oman (UTC+4)
    'DXB': -1.5,   # Dubai, UAE (UTC+4)
    'AUH': -1.5,   # Abu Dhabi, UAE (UTC+4)
    'SHJ': -1.5,   # Sharjah, UAE (UTC+4)
    
    # Southeast Asia
    'BKK': +1.5,   # Bangkok, Thailand (UTC+7)
    'HAN': +1.5,   # Hanoi, Vietnam (UTC+7)
    'SGN': +1.5,   # Ho Chi Minh City, Vietnam (UTC+7)
    'SIN': +2.5,   # Singapore (UTC+8)
    'KUL': +2.5,   # Kuala Lumpur, Malaysia (UTC+8)
    'DPS': +2.5,   # Bali/Denpasar, Indonesia (UTC+8)
    'CGK': +1.5,   # Jakarta, Indonesia (UTC+7)
    'HKG': +2.5,   # Hong Kong (UTC+8)
    'PVG': +2.5,   # Shanghai, China (UTC+8)
    'PEK': +2.5,   # Beijing, China (UTC+8)
    'ICN': +3.5,   # Seoul, South Korea (UTC+9)
    'NRT': +3.5,   # Tokyo Narita, Japan (UTC+9)
    'HND': +3.5,   # Tokyo Haneda, Japan (UTC+9)
    'MNL': +2.5,   # Manila, Philippines (UTC+8)
    'RGN': +1.0,   # Yangon, Myanmar (UTC+6:30)
    
    # South Asia (same or close to IST)
    'CMB': 0,      # Colombo, Sri Lanka (UTC+5:30)
    'MLE': 0,      # Male, Maldives (UTC+5)
    'KTM': +0.25,  # Kathmandu, Nepal (UTC+5:45)
    'DAC': +0.5,   # Dhaka, Bangladesh (UTC+6)
    
    # Europe
    'LHR': -5.5,   # London (UTC+0, winter)
    'CDG': -4.5,   # Paris (UTC+1, winter)
    'FRA': -4.5,   # Frankfurt (UTC+1, winter)
    'AMS': -4.5,   # Amsterdam (UTC+1, winter)
    
    # Central Asia
    'TAS': -0.5,   # Tashkent, Uzbekistan (UTC+5)
    'ALA': +0.5,   # Almaty, Kazakhstan (UTC+6)
}

# ============================================================================
# INDIAN AIRPORTS (Default to IST, offset = 0)
# ============================================================================

INDIAN_AIRPORTS = {
    'DEL', 'BOM', 'MAA', 'CCU', 'BLR', 'HYD', 'AMD', 'COK', 'GOI', 'PNQ',
    'JAI', 'LKO', 'PAT', 'GAU', 'IXB', 'IXC', 'IXE', 'SXR', 'ATQ', 'VNS',
    'NAG', 'IDR', 'BBI', 'RPR', 'RAI', 'VTZ', 'TRZ', 'CJB', 'IXM', 'CCJ',
    'TRV', 'STV', 'BDQ', 'UDR', 'JDH', 'GWL', 'BHO', 'IXR', 'DED', 'DHM',
    'IXA', 'IXS', 'IMF', 'DIB', 'JRH', 'AJL', 'PYG', 'IXZ', 'AGR', 'VGA',
    'PNY', 'IXJ', 'IXL', 'IXU', 'IXY', 'JSA', 'JGA', 'KNU', 'KLH',
    'KUU', 'IXK', 'BJP', 'BHJ', 'BHU', 'BEK', 'BEP', 'CDP',
}


def is_domestic_airport(airport_code: str) -> bool:
    """
    Check if an airport is a domestic Indian airport.
    
    Args:
        airport_code: 3-letter IATA airport code
        
    Returns:
        True if domestic, False if international
    """
    airport_code = airport_code.strip().upper()
    
    # If it's in the international timezone list, it's international
    if airport_code in AIRPORT_TIMEZONE_OFFSET_FROM_IST:
        return False
    
    # If it's in the Indian airports list, it's domestic
    if airport_code in INDIAN_AIRPORTS:
        return True
    
    # Codes starting with 'IX' are typically Indian
    if airport_code.startswith('IX'):
        return True
    
    # Default: assume domestic if not in international list
    return airport_code not in AIRPORT_TIMEZONE_OFFSET_FROM_IST

