import os
import open3d as o3d
import numpy as np
import trimesh
from scan_parser import MeshProcessor
from scipy.spatial import ConvexHull
from annotation_utils import BoundingBoxAnnotator
from object_clustering import object_clusters, process_clusters_with_annotator

# --- Load STL mesh ---
processor = MeshProcessor("toiletries.stl")
mesh = processor.mesh

# DON'T scale the mesh directly - causes segfault on macOS
# Instead apply scale factor to calculations
ENABLE_SCALING = False  # Global toggle for scaling
base_scale_factor = 100
scale_factor = base_scale_factor if ENABLE_SCALING else 1

print(f"Configuration: ENABLE_SCALING={ENABLE_SCALING}, scale_factor={scale_factor}")

# --- Convert to Trimesh for easier measurements ---
tri_mesh = trimesh.Trimesh(vertices=np.asarray(mesh.vertices),
                           faces=np.asarray(mesh.triangles))
print(tri_mesh)

# Initialize the bounding box annotator
annotator = BoundingBoxAnnotator()


# --- 1. Floor Plane Detection ---
def floor_plane_ransac(mesh, distance_threshold=0.01, ransac_n=3, num_iterations=1000):
    points = np.asarray(mesh.vertices)
    # Convert mesh to point cloud for plane segmentation
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    # RANSAC plane fitting
    plane_model, inliers = pcd.segment_plane(distance_threshold=distance_threshold,
                                            ransac_n=ransac_n,
                                            num_iterations=num_iterations)
    [a, b, c, d] = plane_model
    print(f"Plane equation: {a:.2f}x + {b:.2f}y + {c:.2f}z + {d:.2f} = 0")
    return plane_model, inliers

plane_model, inliers = floor_plane_ransac(mesh)

# Add plane annotation to annotator
plane_points = np.asarray(mesh.vertices)[inliers]
annotator.add_plane_annotation(plane_points, plane_model, "floor_plane")


def plane_min_width(mesh, inliers, scale_factor=0.001):
    floor_xy = np.asarray(mesh.vertices)[inliers][:, :2]  # Extract XY of inliers
    if len(floor_xy) < 3:
        print("Not enough points to compute convex hull.")
        return None
    hull = ConvexHull(floor_xy)
    hull_points = floor_xy[hull.vertices]
    
    # Compute pairwise distances to find min width
    min_width = np.min([np.linalg.norm(hull_points[i] - hull_points[j])
                         for i in range(len(hull_points))
                         for j in range(i + 1, len(hull_points))])
    
    # Apply scale factor (will be 1 if scaling disabled)
    return min_width * scale_factor

# Process clusters and add to annotations
labels = object_clusters(mesh)
process_clusters_with_annotator(mesh, labels, annotator, scale_factor=scale_factor)

# Export all annotations
annotator.export_annotations("output/object_annotations.json")