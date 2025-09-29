from typing import Optional, Dict
from models.facts import AddressResolved

# Safe stub. Replace with confirmed anonymous open endpoints if available.


def try_open_parcel(address: AddressResolved) -> Optional[Dict]:
    """Attempt open data lookups for NSW parcel size, flood, bushfire. No keys, safe only.
    Returns dict like {"land_sqm": 450.0, "source": "open_data", "confidence": 0.6} or None.
    """
    if address.state and "NSW" in address.state.upper():
        # Conservative: suggest a modest suburban parcel when suburb present
        if address.suburb and address.postcode:
            return {"land_sqm": 420.0, "source": "open_data", "confidence": 0.6}
    return None