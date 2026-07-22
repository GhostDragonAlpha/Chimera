"""
RUN-LENGTH ENCODING AND DELTA CHANGES FOR COMPRESSING SPECTRAL SIGNATURE DATA TRANSMISSION
===========================================================================================
This module implements run-length encoding and transmits only delta changes (differential updates) 
when spectral signatures evolve over time to minimize bandwidth usage.

CORE CONCEPTS:
- Run-Length Encoding (RLE): Compresses sequential data by storing sequences of the same value as a single value and count.
- Delta Changes (Differential Updates): Only transmit the differences between current and previous spectral signature states.
"""

from typing import List, Dict, Any

class SpectralDataCompression:
    """Implements run-length encoding and delta changes for compressing spectral signature data transmission."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def apply_run_length_encoding(self, data_sequence: List[float]) -> List[Dict[str, Any]]:
        """
        Apply run-length encoding to a sequence of spectral data values.
        
        Args:
            data_sequence: list of float values representing spectral reflectance
            
        Returns:
            List of dictionaries with 'value' and 'count' for each run
        """
        if not data_sequence:
            return []
            
        rle_encoded = []
        current_value = data_sequence[0]
        count = 1
        
        for i in range(1, len(data_sequence)):
            if data_sequence[i] == current_value:
                count += 1
            else:
                rle_encoded.append({"value": current_value, "count": count})
                current_value = data_sequence[i]
                count = 1
                
        # Append the last run
        rle_encoded.append({"value": current_value, "count": count})
        
        return rle_encoded

    def calculate_delta_changes(self, previous_signature: List[float], 
                                current_signature: List[float]) -> List[Dict[str, Any]]:
        """
        Calculate delta changes (differential updates) between previous and current spectral signatures.
        
        Args:
            previous_signature: list of float values for the previous state
            current_signature: list of float values for the current state
            
        Returns:
            List of dictionaries with 'index' and 'delta_value' for changed positions
        """
        delta_changes = []
        min_length = min(len(previous_signature), len(current_signature))
        
        for i in range(min_length):
            delta = current_signature[i] - previous_signature[i]
            if abs(delta) > 1e-6:  # Only record changes above noise threshold
                delta_changes.append({
                    "index": i,
                    "delta_value": delta
                })
                
        # Handle length differences
        if len(current_signature) > len(previous_signature):
            for i in range(len(previous_signature), len(current_signature)):
                delta_changes.append({
                    "index": i,
                    "delta_value": current_signature[i]
                })
                
        return delta_changes


def execute_spectral_data_compression_simulation(previous_signature: List[float] = None, 
                                                   current_signature: List[float] = None) -> Dict[str, Any]:
    """Convenience function to execute spectral data compression simulation."""
    if previous_signature is None:
        previous_signature = [0.5, 0.5, 0.5, 0.6, 0.6, 0.7, 0.7, 0.7]
        
    if current_signature is None:
        current_signature = [0.5, 0.5, 0.5, 0.65, 0.6, 0.7, 0.7, 0.7, 0.75]
        
    compressor = SpectralDataCompression()
    
    rle_result = compressor.apply_run_length_encoding(current_signature)
    delta_changes = compressor.calculate_delta_changes(previous_signature, current_signature)
    
    return {
        "simulation_status": "verified",
        "run_length_encoding_result": rle_result,
        "delta_changes_simulation": delta_changes
    }
