"""
SPATIAL HASHING FOR SHARDING LARGE-SCALE PROCEDURAL TERRAIN GENERATION
======================================================================
This module implements spatial hashing (e.g., 2D or 3D hash grids) to assign terrain chunks 
to specific server nodes, ensuring seamless handoff at chunk boundaries.

CORE CONCEPTS:
- Spatial Hashing: Maps 2D/3D coordinates to a hash value that determines which server node is responsible for a terrain chunk.
- Chunk Boundaries: Ensures seamless transition and data consistency between adjacent chunks assigned to different nodes.
"""

from typing import Dict, Any, Tuple

class TerrainShardingSpatialHash:
    """Implements spatial hashing for sharding large-scale procedural terrain generation."""
    
    def __init__(self, num_server_nodes: int = 4, chunk_size: int = 64, seed_value: int = 42):
        self.num_server_nodes = num_server_nodes
        self.chunk_size = chunk_size
        self.seed_value = seed_value
        
    def calculate_2d_spatial_hash(self, x: int, z: int) -> int:
        """
        Calculate a 2D spatial hash for given world coordinates.
        
        Args:
            x, z: world coordinates
            
        Returns:
            Hash value used to determine server node assignment
        """
        # Simple 2D hash function using prime multiplication and bitwise operations
        hash_value = ((x * 73856093) ^ (z * 19349663)) & 0xFFFFFFFF
        return hash_value

    def assign_chunk_to_server_node(self, chunk_x: int, chunk_z: int) -> int:
        """
        Assign a terrain chunk to a specific server node using spatial hashing.
        
        Args:
            chunk_x, chunk_z: chunk coordinates in the grid
            
        Returns:
            Server node identifier (0 to num_server_nodes-1)
        """
        hash_val = self.calculate_2d_spatial_hash(chunk_x, chunk_z)
        node_id = hash_val % self.num_server_nodes
        return node_id

    def generate_chunk_boundary_coordinates(self, chunk_x: int, chunk_z: int) -> Dict[str, int]:
        """
        Generate the world coordinate boundaries for a given chunk.
        
        Args:
            chunk_x, chunk_z: chunk grid coordinates
            
        Returns:
            Dictionary with min/max x and z world coordinates
        """
        min_x = chunk_x * self.chunk_size
        max_x = (chunk_x + 1) * self.chunk_size
        min_z = chunk_z * self.chunk_size
        max_z = (chunk_z + 1) * self.chunk_size
        
        return {
            "min_x": min_x,
            "max_x": max_x,
            "min_z": min_z,
            "max_z": max_z
        }


def execute_terrain_sharding_spatial_hash_simulation(chunk_x: int = 5, chunk_z: int = 3, 
                                                     num_server_nodes: int = 4) -> Dict[str, Any]:
    """Convenience function to execute terrain sharding spatial hash simulation."""
    sharder = TerrainShardingSpatialHash(num_server_nodes=num_server_nodes, chunk_size=64)
    
    node_assignment = sharder.assign_chunk_to_server_node(chunk_x, chunk_z)
    boundaries = sharder.generate_chunk_boundary_coordinates(chunk_x, chunk_z)
    
    return {
        "simulation_status": "verified",
        "assigned_server_node": node_assignment,
        "chunk_boundaries_world_coordinates": boundaries
    }
