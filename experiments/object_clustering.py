import os
import open3d as o3d
import numpy as np
import trimesh
from scan_parser import MeshProcessor
from annotation_utils import BoundingBoxAnnotator
from floor_plane import find_lowest_plane


class ClusterFilterRules:
    """Rule set for filtering noisy clusters"""
    
    def __init__(self):
        self.min_points = 50         # Reduced from 100
        self.max_points = 75000     # Increased from 50000
        self.min_volume = 0.00001    # Reduced from 0.0001
        self.max_volume = 50.0       # Increased from 10.0
        self.min_dimension = 0.005   # Reduced from 0.01
        self.max_dimension = 10.0    # Increased from 5.0
        self.max_aspect_ratio = 50.0 # Increased from 20.0
        self.min_density = 10        # Reduced from 50
        
    def apply_size_filters(self, cluster_points):
        """Apply size-based filters"""
        point_count = len(cluster_points)
        
        # Filter by point count
        if point_count < self.min_points or point_count > self.max_points:
            return False, f"Point count {point_count} outside range [{self.min_points}, {self.max_points}]"
        
        # Calculate bounding box
        min_bound = cluster_points.min(axis=0)
        max_bound = cluster_points.max(axis=0)
        dimensions = max_bound - min_bound
        
        # Filter by individual dimensions
        if np.any(dimensions < self.min_dimension):
            return False, f"Dimension too small: {dimensions}"
        
        if np.any(dimensions > self.max_dimension):
            return False, f"Dimension too large: {dimensions}"
        
        # Filter by volume
        volume = np.prod(dimensions)
        if volume < self.min_volume or volume > self.max_volume:
            return False, f"Volume {volume:.6f} outside range [{self.min_volume}, {self.max_volume}]"
        
        return True, "Size filters passed"
    
    def apply_shape_filters(self, cluster_points):
        """Apply shape-based filters"""
        min_bound = cluster_points.min(axis=0)
        max_bound = cluster_points.max(axis=0)
        dimensions = max_bound - min_bound
        
        # Filter by aspect ratio (avoid extremely elongated objects)
        max_dim = np.max(dimensions)
        min_dim = np.min(dimensions[dimensions > 0])  # Avoid division by zero
        
        if min_dim > 0:
            aspect_ratio = max_dim / min_dim
            if aspect_ratio > self.max_aspect_ratio:
                return False, f"Aspect ratio {aspect_ratio:.2f} exceeds {self.max_aspect_ratio}"
        
        return True, "Shape filters passed"
    
    def apply_density_filters(self, cluster_points):
        """Apply density-based filters"""
        min_bound = cluster_points.min(axis=0)
        max_bound = cluster_points.max(axis=0)
        dimensions = max_bound - min_bound
        volume = np.prod(dimensions)
        
        if volume > 0:
            density = len(cluster_points) / volume
            if density < self.min_density:
                return False, f"Density {density:.2f} below minimum {self.min_density}"
        
        return True, "Density filters passed"
    
    def apply_geometric_filters(self, cluster_points):
        """Apply geometric coherence filters"""
        # Check if cluster is too scattered (high variance relative to size)
        center = cluster_points.mean(axis=0)
        distances = np.linalg.norm(cluster_points - center, axis=1)
        std_distance = np.std(distances)
        mean_distance = np.mean(distances)
        
        # Coefficient of variation for distance spread
        if mean_distance > 0:
            cv_distance = std_distance / mean_distance
            if cv_distance > 1.5:  # Highly scattered cluster
                return False, f"Cluster too scattered (CV: {cv_distance:.2f})"
        
        return True, "Geometric filters passed"
    
    def is_bbox_enclosed(self, smaller_points, larger_points, tolerance=0.01):
        """Check if smaller bounding box is completely enclosed within larger one"""
        smaller_min = smaller_points.min(axis=0)
        smaller_max = smaller_points.max(axis=0)
        larger_min = larger_points.min(axis=0)
        larger_max = larger_points.max(axis=0)
        
        # Check if smaller bbox is completely inside larger bbox (with tolerance)
        enclosed = (np.all(smaller_min >= larger_min - tolerance) and 
                   np.all(smaller_max <= larger_max + tolerance))
        
        return enclosed
    
    def apply_enclosure_filters(self, cluster_points, all_cluster_data):
        """Filter out clusters that are enclosed within larger clusters"""
        current_min = cluster_points.min(axis=0)
        current_max = cluster_points.max(axis=0)
        current_volume = np.prod(current_max - current_min)
        
        for other_id, other_points in all_cluster_data:
            other_min = other_points.min(axis=0)
            other_max = other_points.max(axis=0)
            other_volume = np.prod(other_max - other_min)
            
            # Only check against larger clusters
            if other_volume > current_volume:
                if self.is_bbox_enclosed(cluster_points, other_points):
                    return False, f"Enclosed within larger cluster {other_id}"
        
        return True, "Enclosure filters passed"
    
    def apply_floor_plane_filters(self, cluster_points, floor_2d_bounds, floor_tolerance=0.3):
        """Filter to keep clusters that have X-Z overlap with the 2D floor plane area"""
        if floor_2d_bounds is None:
            return True, "No 2D floor plane reference available"
        
        # Get X-Z bounds of cluster (ignoring Y/height)
        cluster_min_xz = cluster_points[:, [0, 2]].min(axis=0)  # [X_min, Z_min]
        cluster_max_xz = cluster_points[:, [0, 2]].max(axis=0)  # [X_max, Z_max]
        
        # Get 2D floor bounds
        floor_x_min = floor_2d_bounds['x_min']
        floor_x_max = floor_2d_bounds['x_max']
        floor_z_min = floor_2d_bounds['z_min']
        floor_z_max = floor_2d_bounds['z_max']
        
        # Check for overlap in X-Z plane (2D rectangle overlap)
        # Two rectangles overlap if they overlap in both X and Z dimensions
        x_overlap = (cluster_max_xz[0] >= floor_x_min - floor_tolerance and 
                    cluster_min_xz[0] <= floor_x_max + floor_tolerance)
        z_overlap = (cluster_max_xz[1] >= floor_z_min - floor_tolerance and 
                    cluster_min_xz[1] <= floor_z_max + floor_tolerance)
        
        has_xz_overlap = x_overlap and z_overlap
        
        if not has_xz_overlap:
            return False, f"No X-Z overlap with 2D floor (cluster: X[{cluster_min_xz[0]:.3f}, {cluster_max_xz[0]:.3f}], Z[{cluster_min_xz[1]:.3f}, {cluster_max_xz[1]:.3f}])"
        
        return True, f"Has X-Z overlap with 2D floor plane"
    
    def filter_cluster(self, cluster_points, cluster_id, verbose=False, all_cluster_data=None, floor_2d_bounds=None):
        """Apply all filter rules to a cluster"""
        filters = [
            self.apply_size_filters,
            self.apply_shape_filters, 
            self.apply_density_filters,
            self.apply_geometric_filters
        ]
        
        # Apply basic filters first
        for filter_func in filters:
            passed, message = filter_func(cluster_points)
            if not passed:
                if verbose:
                    print(f"Cluster {cluster_id} filtered out: {message}")
                return False
        
        # Apply 2D floor plane filter if floor bounds are available
        if floor_2d_bounds is not None:
            passed, message = self.apply_floor_plane_filters(cluster_points, floor_2d_bounds)
            if not passed:
                if verbose:
                    print(f"Cluster {cluster_id} filtered out: {message}")
                return False
        
        # Apply enclosure filter if we have data about other clusters
        if all_cluster_data is not None:
            passed, message = self.apply_enclosure_filters(cluster_points, all_cluster_data)
            if not passed:
                if verbose:
                    print(f"Cluster {cluster_id} filtered out: {message}")
                return False
        
        if verbose:
            print(f"Cluster {cluster_id} passed all filters")
        return True


def object_clusters(mesh, eps=0.02, min_points=10):
    """Cluster mesh vertices using DBSCAN algorithm
    
    Args:
        mesh: Open3D mesh object
        eps: Maximum distance between two samples for clustering
        min_points: Minimum number of points required to form a cluster
    
    Returns:
        labels: Array of cluster labels for each vertex
    """
    points = np.asarray(mesh.vertices)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_points, print_progress=True))
    max_label = labels.max()
    print(f"Point cloud has {max_label + 1} clusters")
    return labels


def process_clusters_with_annotator(mesh, labels, annotator, scale_factor=1.0, min_cluster_size=50, 
                                   use_filters=True, verbose=False, floor_2d_bounds=None):
    """Process clusters and add them to the annotator with optional filtering
    
    Args:
        mesh: Open3D mesh object
        labels: Cluster labels from DBSCAN
        annotator: BoundingBoxAnnotator instance
        scale_factor: Scale factor for coordinates
        min_cluster_size: Minimum points required for a cluster to be annotated
        use_filters: Whether to apply noise reduction filters
        verbose: Whether to print detailed filtering information
        floor_2d_bounds: 2D bounds dict for X-Z overlap filtering
    """
    points = np.asarray(mesh.vertices)
    filter_rules = ClusterFilterRules() if use_filters else None
    
    # First pass: collect all valid clusters (before enclosure filtering)
    valid_clusters = []
    for i in range(labels.max() + 1):
        cluster_points = points[labels == i]
        if cluster_points.size == 0 or len(cluster_points) < min_cluster_size:
            continue
        
        # Apply basic filters (size, shape, density, geometric) and 2D floor filter
        if use_filters and filter_rules:
            if filter_rules.filter_cluster(cluster_points, i, verbose=True, all_cluster_data=None, floor_2d_bounds=floor_2d_bounds):
                valid_clusters.append((i, cluster_points))
        else:
            valid_clusters.append((i, cluster_points))
    
    # Second pass: apply enclosure filtering
    filtered_count = 0
    processed_count = 0
    
    for cluster_id, cluster_points in valid_clusters:
        # Apply enclosure filter with data about all other valid clusters
        if use_filters and filter_rules:
            other_clusters = [(other_id, other_points) for other_id, other_points in valid_clusters 
                            if other_id != cluster_id]
            
            if not filter_rules.filter_cluster(cluster_points, cluster_id, verbose, other_clusters, floor_2d_bounds):
                filtered_count += 1
                continue
        
        processed_count += 1
        print(f"Processing cluster {cluster_id}: {len(cluster_points)} points")
        annotator.add_cluster_annotation(cluster_points, cluster_id, scale_factor)
    
    if use_filters:
        print(f"Filtering results: {processed_count} clusters kept, {filtered_count} filtered out")


def analyze_object_clusters(mesh_path, scale_factor=1.0, eps=1.0, min_samples=10, 
                          annotation_folder="annotations", output_suffix="clusters",
                          use_filters=True, verbose=False):
    """
    Complete object clustering pipeline with 2D floor plane approach
    
    Args:
        mesh_path: Path to mesh file
        scale_factor: Scale factor for coordinates
        eps: DBSCAN epsilon parameter
        min_samples: DBSCAN min_samples parameter
        annotation_folder: Folder to save annotations
        output_suffix: Suffix for annotation filename
        use_filters: Whether to apply noise reduction filters
        verbose: Whether to print detailed filtering information
        
    Returns:
        tuple: (num_clusters, num_filtered_clusters, floor_2d_bounds)
    """
    print(f"Loading mesh from: {mesh_path}")
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    
    if len(mesh.vertices) == 0:
        raise ValueError(f"Could not load mesh from {mesh_path}")
    
    print(f"Mesh loaded with {len(mesh.vertices)} vertices")
    
    # Create 2D floor plane from mesh X-Z bounds
    print("\n--- 2D FLOOR PLANE CREATION ---")
    points = np.asarray(mesh.vertices)
    
    # Get X-Z bounds of entire mesh (ignoring Y)
    x_coords = points[:, 0]
    z_coords = points[:, 2]
    
    floor_2d_bounds = {
        'x_min': np.min(x_coords),
        'x_max': np.max(x_coords),
        'z_min': np.min(z_coords),
        'z_max': np.max(z_coords)
    }
    
    # Add small buffer to ensure coverage
    buffer = 0.1
    floor_2d_bounds['x_min'] -= buffer
    floor_2d_bounds['x_max'] += buffer
    floor_2d_bounds['z_min'] -= buffer
    floor_2d_bounds['z_max'] += buffer
    
    print(f"2D Floor plane bounds:")
    print(f"  X range: [{floor_2d_bounds['x_min']:.3f}, {floor_2d_bounds['x_max']:.3f}]")
    print(f"  Z range: [{floor_2d_bounds['z_min']:.3f}, {floor_2d_bounds['z_max']:.3f}]")
    
    # For annotation display, find the actual lowest surface
    from floor_plane import find_lowest_plane
    pcd = mesh.sample_points_uniformly(number_of_points=10000)
    plane_model, inliers = find_lowest_plane(pcd)
    
    if plane_model is not None and inliers is not None:
        floor_points_for_annotation = np.asarray(pcd.points)[inliers]
        floor_height = np.mean(floor_points_for_annotation[:, 1])
        print(f"Floor height for display: {floor_height:.4f}")
    else:
        floor_points_for_annotation = None
        floor_height = None
    
    # Perform clustering
    print("\n--- OBJECT CLUSTERING ---")
    points = np.asarray(mesh.vertices)
    labels = perform_dbscan_clustering(points, eps=eps, min_samples=min_samples)
    
    num_clusters = labels.max() + 1 if labels.max() >= 0 else 0
    print(f"\nDBSCAN clustering found {num_clusters} clusters")
    
    # Setup annotation system
    os.makedirs(annotation_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(mesh_path))[0]
    output_filename = f"{base_name}_{output_suffix}.json"
    output_path = os.path.join(annotation_folder, output_filename)
    
    annotator = BoundingBoxAnnotator()
    
    # Add floor plane annotation if detected (for display purposes)
    if floor_points_for_annotation is not None and plane_model is not None:
        annotator.add_plane_annotation(floor_points_for_annotation, plane_model, "floor")
    
    # Process clusters with 2D floor plane filtering
    initial_cluster_count = num_clusters
    process_clusters_with_annotator(mesh, labels, annotator, scale_factor, 
                                  use_filters=use_filters, verbose=verbose,
                                  floor_2d_bounds=floor_2d_bounds)
    
    # Export results
    annotator.export_annotations(output_path)
    final_cluster_count = len([ann for ann in annotator.annotations if ann['annotation_type'] == 'cluster'])
    
    print(f"\nClustering completed:")
    print(f"- Initial clusters: {initial_cluster_count}")
    print(f"- Final clusters (after filtering): {final_cluster_count}")
    if use_filters and initial_cluster_count > 0:
        reduction_percent = ((initial_cluster_count - final_cluster_count) / initial_cluster_count) * 100
        print(f"- Noise reduction: {reduction_percent:.1f}%")
    print(f"- Annotations saved to: {output_path}")
    
    return num_clusters, final_cluster_count, floor_2d_bounds


def perform_dbscan_clustering(points, eps=1.0, min_samples=10):
    """Perform DBSCAN clustering on point cloud
    
    Args:
        points: Numpy array of 3D points
        eps: Maximum distance between samples for clustering
        min_samples: Minimum number of samples in a neighborhood
    
    Returns:
        labels: Array of cluster labels (-1 for noise)
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    
    labels = np.array(pcd.cluster_dbscan(eps=eps, min_points=min_samples, print_progress=True))
    
    n_clusters = labels.max() + 1 if labels.max() >= 0 else 0
    n_noise = list(labels).count(-1)
    
    print(f"DBSCAN found {n_clusters} clusters and {n_noise} noise points")
    return labels


# Test the integrated floor plane detection and object clustering
if __name__ == "__main__":
    # Test with room.stl file
    mesh_path = "../data/room.stl"

    if not os.path.exists(mesh_path):
        print(f"Mesh file not found: {mesh_path}")
        print("Available files in ../data/:")
        data_dir = "../data"
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith(('.ply', '.stl', '.obj')):
                    print(f"  - {file}")
        exit(1)
    
    print("Testing integrated floor plane detection + object clustering...")
    print("="*60)
    
    # Run analysis with 2D floor plane integration
    num_clusters, final_clusters, floor_2d_bounds = analyze_object_clusters(
        mesh_path=mesh_path,
        scale_factor=1.0,
        eps=0.1,  # Smaller eps for more detailed clustering
        min_samples=20,  # Lower min_samples for more clusters
        annotation_folder="../data/annotations",
        output_suffix="2d_floor_clusters",
        use_filters=True,
        verbose=True
    )
    
    print("="*60)
    print("2D FLOOR PLANE RESULTS:")
    if floor_2d_bounds is not None:
        x_range = floor_2d_bounds['x_max'] - floor_2d_bounds['x_min']
        z_range = floor_2d_bounds['z_max'] - floor_2d_bounds['z_min']
        floor_area = x_range * z_range
        print(f"- 2D Floor area: {floor_area:.2f} square units")
        print(f"- X range: {x_range:.2f}, Z range: {z_range:.2f}")
    else:
        print("- No 2D floor plane created")
    print(f"- Total clusters found: {num_clusters}")
    print(f"- Clusters with X-Z overlap: {final_clusters}")
    if num_clusters > 0:
        overlap_percent = (final_clusters / num_clusters) * 100
        print(f"- X-Z overlap ratio: {overlap_percent:.1f}%")
    
    # Load and visualize results
    try:
        from scan_parser import MeshProcessor
        processor = MeshProcessor(mesh_path)
        
        # Load annotations - use the correct file based on the input mesh
        base_name = os.path.splitext(os.path.basename(mesh_path))[0]
        annotation_path = f"../data/annotations/{base_name}_2d_floor_clusters.json"
        if os.path.exists(annotation_path):
            import json
            with open(annotation_path, 'r') as f:
                annotation_data = json.load(f)
            
            # Extract the annotations list from the JSON structure
            annotations = annotation_data.get('annotations', [])
            
            print(f"\nLoaded {len(annotations)} annotations for visualization")
            processor.visualize_mesh_with_annotations_overlayed(annotations, line_thickness=0.02)
        else:
            print(f"Annotation file not found: {annotation_path}")
            processor.visualize_mesh()
            
    except ImportError:
        print("Could not import MeshProcessor for visualization")
    except Exception as e:
        print(f"Visualization error: {e}")
