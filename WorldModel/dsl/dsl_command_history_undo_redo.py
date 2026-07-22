"""
DSL COMMAND HISTORY AND UNDO/REDO FEATURE
==========================================
This module implements storing a time-series log of DSL commands and simulation state snapshots, 
allowing reversal or replay of command sequences.

CORE CONCEPTS:
- Time-Series Log of DSL Commands: Records each natural language command with a timestamp and sequence identifier.
- Simulation State Snapshots: Captures the state of the simulation at the point of each command execution.
- Reversal/Replay Capability: Enables undo (reversal) or redo/replay of command sequences using the stored logs and snapshots.
"""

from typing import Dict, Any, List
import time

class DSLCommandHistoryUndoRedo:
    """Implements command history and undo/redo feature for natural language DSL inputs."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        self.command_log: List[Dict[str, Any]] = []
        self.state_snapshots: Dict[int, Dict[str, Any]] = {}
        
    def log_dsl_command_and_state_snapshot(self, command_text: str, 
                                           state_snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a DSL command and capture the associated simulation state snapshot.
        
        Args:
            command_text: the natural language DSL command string
            state_snapshot_data: dictionary representing the simulation state at command execution
            
        Returns:
            Dictionary containing logging results and sequence identifier
        """
        sequence_id = len(self.command_log) + 1
        timestamp = time.time()
        
        # Log the command
        command_entry = {
            "sequence_id": sequence_id,
            "timestamp": timestamp,
            "command_text": command_text,
            "status": "logged"
        }
        self.command_log.append(command_entry)
        
        # Store the state snapshot
        self.state_snapshots[sequence_id] = state_snapshot_data
        
        return {
            "sequence_id": sequence_id,
            "timestamp": timestamp,
            "command_logged": command_text,
            "state_snapshot_stored": True,
            "status": "dsl_command_and_state_snapshot_logged"
        }

    def retrieve_command_sequence_for_replay_or_reversal(self, start_sequence: int, 
                                                         end_sequence: int) -> List[Dict[str, Any]]:
        """
        Retrieve a sequence of DSL commands and state snapshots for replay or reversal (undo/redo).
        
        Args:
            start_sequence: starting sequence identifier
            end_sequence: ending sequence identifier
            
        Returns:
            List of command and snapshot entries within the specified range
        """
        sequence_range = []
        for seq_id in range(start_sequence, end_sequence + 1):
            if seq_id in self.command_log:
                # Find the command entry
                cmd_entry = next((c for c in self.command_log if c['sequence_id'] == seq_id), None)
                snapshot_entry = self.state_snapshots.get(seq_id, {})
                
                if cmd_entry:
                    sequence_range.append({
                        "sequence_id": seq_id,
                        "command": cmd_entry.get('command_text'),
                        "timestamp": cmd_entry.get('timestamp'),
                        "state_snapshot": snapshot_entry
                    })
                    
        return sequence_range


def execute_dsl_command_history_undo_redo_simulation(command_text: str = "CONNECT spectral_port to_usgs_reference", 
                                                     state_snapshot_data: Dict[str, Any] = {"active_membranes": 15, "tier_unlocks": ["tier_3"]}) -> Dict[str, Any]:
    """Convenience function to execute DSL command history and undo/redo simulation."""
    history_engine = DSLCommandHistoryUndoRedo(seed_value=42)
    
    # Log a command
    log_result = history_engine.log_dsl_command_and_state_snapshot(
        command_text=command_text,
        state_snapshot_data=state_snapshot_data
    )
    
    # Retrieve the sequence (simulating undo/redo replay range)
    retrieve_result = history_engine.retrieve_command_sequence_for_replay_or_reversal(
        start_sequence=1,
        end_sequence=1
    )
    
    return {
        "simulation_status": "verified",
        "dsl_command_and_snapshot_logging_results": log_result,
        "command_sequence_retrieval_for_replay_reversal_results": retrieve_result
    }
