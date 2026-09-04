import os
import open3d as o3d
import numpy as np
import trimesh
from scan_parser import MeshProcessor
from scipy.spatial import ConvexHull

from annotation_utils import BoundingBoxAnnotator


WALKWAY_MAX_PLANES = 5

def find_lowest_plane(pcd):
    """Find the actual lowest plane with reasonable noise reduction for rough room scans"""
    distance_threshold = 0.03  # Slightly increased for noisy scan data
    ransac_n = 3
    num_iterations = 1500  # More iterations for better accuracy with noise
    max_planes_to_check = 6
    
    lowest_plane = None
    lowest_inliers = None
    lowest_height = float('inf')
    best_quality = 0
    
    remaining_pcd = pcd
    
    print("Searching for floor plane with noise reduction...")
    
    # Try to find multiple planes and pick the best one based on quality
    for i in range(max_planes_to_check):
        if len(remaining_pcd.points) < 300:  # Reduced for rough scans
            break
            
        plane_model, inliers = remaining_pcd.segment_plane(distance_threshold=distance_threshold,
                                                         ransac_n=ransac_n,
                                                         num_iterations=num_iterations)
        
        if len(inliers) < 300:  # Reduced minimum points
            break
        
        # Get the points that belong to this plane
        plane_points = np.asarray(remaining_pcd.points)[inliers]
        
        # Calculate the average Y coordinate (height) of the plane points
        avg_height = np.mean(plane_points[:, 1])
        
        # Quality assessment for rough scans
        normal = np.array(plane_model[:3])
        normal = normal / np.linalg.norm(normal)
        
        # Check if plane is reasonably horizontal (more lenient for rough scans)
        horizontal_score = abs(normal[1])  # Y-component should be high for horizontal planes
        
        # Calculate plane quality metrics
        area_estimate = calculate_rough_area(plane_points)
        point_density = len(inliers) / max(area_estimate, 0.1)
        
        # Combined quality score (balanced for rough scans)
        quality_score = (
            len(inliers) * 0.4 +           # Point count (40% weight)
            horizontal_score * 1000 +      # Horizontal orientation (high weight)
            min(area_estimate, 5.0) * 200  # Area (capped to avoid huge influence)
        )
        
        print(f"Plane {i}: {len(inliers)} points, height {avg_height:.3f}, "
              f"horizontal {horizontal_score:.2f}, area {area_estimate:.2f}, quality {quality_score:.1f}")
        
        # Selection criteria optimized for rough scans
        is_good_floor_candidate = (
            avg_height <= lowest_height + 0.15 and  # Within reasonable height range
            horizontal_score > 0.7 and              # Reasonably horizontal (lenient)
            area_estimate > 0.3 and                 # Reasonable floor area
            len(inliers) > 500 and                  # Substantial point count
            quality_score > best_quality
        )
        
        if is_good_floor_candidate:
            lowest_height = avg_height
            lowest_plane = plane_model
            lowest_inliers = inliers
            best_quality = quality_score
            print(f"  -> New best floor candidate")
        
        # Remove this plane's points and continue searching
        remaining_pcd = remaining_pcd.select_by_index(inliers, invert=True)
    
    if lowest_plane is not None:
        print(f"\nSelected floor plane at height {lowest_height:.3f}")
        print(f"Plane equation: {lowest_plane[0]:.3f}x + {lowest_plane[1]:.3f}y + {lowest_plane[2]:.3f}z + {lowest_plane[3]:.3f} = 0")
        
        # Apply noise reduction to the selected plane
        cleaned_inliers = apply_reasonable_noise_reduction(pcd, lowest_plane, lowest_inliers, distance_threshold)
        
        return lowest_plane, cleaned_inliers
    
    return None, None


def calculate_rough_area(plane_points):
    """Calculate rough area estimate suitable for noisy scan data"""
    if len(plane_points) < 10:
        return 0
    
    try:
        # Use bounding box area as a rough but robust estimate
        min_coords = np.min(plane_points, axis=0)
        max_coords = np.max(plane_points, axis=0)
        
        # Area in XZ plane (assuming Y is up)
        width = max_coords[0] - min_coords[0]
        depth = max_coords[2] - min_coords[2]
        area = width * depth
        
        return area
    except:
        return 0


def apply_reasonable_noise_reduction(pcd, plane_model, inliers, distance_threshold):
    """Apply reasonable noise reduction suitable for rough room scans"""
    print("Applying noise reduction...")
    
    all_points = np.asarray(pcd.points)
    plane_points = all_points[inliers]
    
    # Create point cloud from plane points
    plane_pcd = o3d.geometry.PointCloud()
    plane_pcd.points = o3d.utility.Vector3dVector(plane_points)
    
    # 1. Statistical outlier removal (moderate parameters for rough scans)
    plane_pcd_clean, stat_inliers = plane_pcd.remove_statistical_outlier(
        nb_neighbors=15,  # Check 15 nearest neighbors
        std_ratio=2.0     # More lenient than default (2.0 vs 1.0)
    )
    print(f"Statistical outlier removal: {len(plane_points)} -> {len(plane_pcd_clean.points)} points")
    
    # 2. Radius outlier removal (remove isolated points)
    plane_pcd_clean, radius_inliers = plane_pcd_clean.remove_radius_outlier(
        nb_points=8,      # At least 8 neighbors
        radius=0.08       # Within 8cm radius (reasonable for room scans)
    )
    print(f"Radius outlier removal: -> {len(plane_pcd_clean.points)} points")
    
    # 3. Re-fit plane to cleaned points with tighter tolerance
    if len(plane_pcd_clean.points) > 200:
        refined_plane, refined_inliers = plane_pcd_clean.segment_plane(
            distance_threshold=distance_threshold * 0.7,  # Slightly tighter
            ransac_n=3,
            num_iterations=800
        )
        
        final_cleaned_points = np.asarray(plane_pcd_clean.points)[refined_inliers]
        print(f"Plane refinement: {len(plane_pcd_clean.points)} -> {len(final_cleaned_points)} points")
        
        # Map cleaned points back to original indices
        final_inliers = []
        for point in final_cleaned_points:
            distances = np.linalg.norm(all_points - point, axis=1)
            closest_idx = np.argmin(distances)
            if distances[closest_idx] < 0.005:  # 5mm tolerance for matching
                final_inliers.append(closest_idx)
        
        return np.array(final_inliers)
    else:
        print("Not enough points after cleaning, using original inliers")
        return inliers


def trim_to_main_floor_region(pcd, inliers, keep_percentage=75):
    """Trim plane to main floor region to remove scattered edge points"""
    plane_points = np.asarray(pcd.points)[inliers]
    
    if len(plane_points) < 100:
        return inliers
    
    # Calculate center and distances
    center = np.median(plane_points, axis=0)  # Use median for robustness
    distances_from_center = np.linalg.norm(plane_points - center, axis=1)
    
    # Keep points within the specified percentage of distances
    distance_threshold = np.percentile(distances_from_center, keep_percentage)
    core_mask = distances_from_center <= distance_threshold
    
    core_inliers = np.array(inliers)[core_mask]
    
    print(f"Floor region trimming: {len(inliers)} -> {len(core_inliers)} points ({keep_percentage}% kept)")
    return core_inliers

# Test the advanced floor plane process
if __name__ == "__main__":
    # Load the bed mesh from data directory
    processor = MeshProcessor("../data/room.stl")
    mesh = processor.mesh
    
    print(f"Loaded mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
    
    if len(mesh.vertices) == 0:
        print("Error: No vertices in mesh")
        exit(1)
    
    # Convert to point cloud for plane detection
    pcd = mesh.sample_points_uniformly(number_of_points=50000)
    print(f"Sampled point cloud with {len(pcd.points)} points")
    
    # Process floor plane - find the lowest plane with noise reduction
    print("Finding precise floor plane...")
    plane_model, inliers = find_lowest_plane(pcd)
    
    if plane_model is None:
        print("No suitable plane found")
        exit(1)
    
    # Apply additional trimming to focus on main floor region
    main_floor_inliers = trim_to_main_floor_region(pcd, inliers, keep_percentage=80)
    
    # Create annotator and add the plane annotation
    annotator = BoundingBoxAnnotator()
    
    # Get points for the main floor region
    plane_points = np.asarray(pcd.points)[main_floor_inliers]
    
    print(f"\nFinal floor plane: {len(plane_points)} points")
    
    # Add plane annotation
    annotator.add_plane_annotation(plane_points, plane_model, "clean_floor_plane")
    
    # Export annotation
    annotator.export_annotations("../data/annotations/clean_floor_plane.json")
    
    # Visualize the mesh with the clean floor plane annotation
    if len(annotator.annotations) > 0:
        processor.visualize_mesh_with_annotations_overlayed(annotator.annotations, line_thickness=0.01)
    else:
        print("No clean floor plane found to visualize")
        # Just show the mesh
        processor.visualize_mesh()

