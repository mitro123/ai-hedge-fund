"""
OpenBB Core Integration pro AI Hedge Fund

Tento modul obsahuje přímou integraci OpenBB Platform komponent
do našeho AI Hedge Fund projektu pro lepší kontrolu a customizaci.
"""

from typing import Optional
import sys
import os

# Přidání OpenBB core do Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    # Import hlavních OpenBB komponent
    from openbb import obb
    
    OPENBB_AVAILABLE = True
    _obb_instance = obb
        
except ImportError as e:
    OPENBB_AVAILABLE = False
    _obb_instance = None
    _import_error = e

def get_obb():
    """Získá OpenBB instanci nebo vyhodí chybu."""
    if OPENBB_AVAILABLE:
        return _obb_instance
    else:
        raise ImportError(f"OpenBB není dostupná: {_import_error}")

__all__ = ["get_obb", "OPENBB_AVAILABLE"]
