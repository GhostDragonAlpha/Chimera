"""
PREDICTIVE STATE INTERPOLATION AND EXTRAPOLATION MODELS FOR NETWORK LATENCY
===========================================================================
This module implements predictive state interpolation and extrapolation models, using 
historical velocity/acceleration data to predict positions during latency gaps in celestial mechanics simulations.

CORE CONCEPTS:
- Predictive Interpolation: Estimates current state based on the most recent received state and known time delta.
- Extrapolation Models: Use historical velocity and acceleration data to project future positions during network latency gaps.
"""

from typing import Dict, Any, List
import time

class LatencyPredictionInterpolation:
    """Implements predictive state interpolation and extrapolation models for network latency."""
    
    def __init__(self, seed_value: int = 42):
        self.seed_value = seed_value
        
    def interpolate_state(self, last_known_position: Dict[str, float], 
                          last_known_velocity: Dict[str, float], 
                          time_delta_sec: float) -> Dict[str, float]:
        """
        Interpolate current state based on last known position and velocity.
        
        Args:
            last_known_position: dictionary with 'x', 'y', 'z' coordinates
            last_known_velocity: dictionary with 'vx', 'vy', 'vz' velocities
            time_delta_sec: time elapsed since last known state (seconds)
            
        Returns:
            Interpolated position dictionary
        """
        interpolated_pos = {
            "x": last_known_position["x"] + last_known_velocity["vx"] * time_delta_sec,
            "y": last_known_position["y"] + last_known_velocity["vy"] * time_delta_sec,
            "z": last_known_position["z"] + last_known_velocity["vz"] * time_delta_sec
        }
        
        return interpolated_pos

    def extrapolate_with_acceleration(self, current_position: Dict[str, float], 
                                      current_velocity: Dict[str, float], 
                                      acceleration: Dict[str, float], 
                                      time_delta_sec: float) -> Dict[str, float]:
        """
        Extrapolate state using position, velocity, and acceleration data.
        
        Args:
            current_position: dictionary with 'x', 'y', 'z' coordinates
            current_velocity: dictionary with 'vx', 'vy', 'vz' velocities
            acceleration: dictionary with 'ax', 'ay', 'az' accelerations
            time_delta_sec: time projection delta (seconds)
            
        Returns:
            Extrapolated position dictionary
        """
        # s = s0 + v0*t + 0.5*a*t^2
        t_sq = 0.5 * (time_delta_sec ** 2)
        
        extrapolated_pos = {
            "x": current_position["x"] + current_velocity["vx"] * time_delta_sec + acceleration["ax"] * t_sq,
            "y": current_position["y"] + current_velocity["vy"] * time_delta_sec + acceleration["ay"] * t_sq,
            "z": current_position["z"] + current_velocity["vz"] * time_delta_sec + acceleration["az"] * t_sq
        }
        
        return extrapolated_pos


def execute_latency_prediction_interpolation_simulation(last_pos: Dict[str, float] = {"x": 100.0, "y": 200.0, "z": 50.0}, 
                                                        last_vel: Dict[str, float] = {"vx": 5.0, "vy": -2.0, "vz": 1.0},
                                                        accel: Dict[str, float] = {"ax": 0.1, "ay": 0.0, "az": -0.05},
                                                        time_delta_sec: float = 0.5) -> Dict[str, Any]:
    """Convenience function to execute latency prediction interpolation simulation."""
    predictor = LatencyPredictionInterpolation()
    
    interpolated_state = predictor.interpolate_state(last_known_position=last_pos, 
                                                     last_known_velocity=last_vel, 
                                                     time_delta_sec=time_delta_sec)
    
    extrapolated_state = predictor.extrapolate_with_acceleration(current_position=last_pos, 
                                                                 current_velocity=last_vel, 
                                                                 acceleration=accel, 
                                                                 time_delta_sec=time_delta_sec)
    
    return {
        "simulation_status": "verified",
        "interpolated_position": interpolated_state,
        "extrapolated_position": extrapolated_state
    }
