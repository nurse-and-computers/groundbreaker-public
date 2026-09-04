import open3d as o3d
import numpy as np
import trimesh
import json
import os

class MeshProcessor:
    def __init__(self, mesh_path):
        """Initialize with mesh file path (supports STL, PLY, OBJ, GLB, etc.)"""
        self.mesh_path = mesh_path
        self.mesh = None
        self.tri_mesh = None
        self.load_mesh()
    
    def load_mesh(self):
        """Load mesh from file (supports STL, PLY, OBJ, GLB, etc.)"""
        try:
            file_ext = self.mesh_path.lower().split('.')[-1]
            
            if file_ext == 'glb':
                # Special handling for GLB files to preserve colors
                print(f"Loading GLB file with Trimesh for color preservation...")
                scene = trimesh.load(self.mesh_path)
                
                if hasattr(scene, 'geometry') and scene.geometry:
                    # Get the first mesh from the scene
                    mesh_name = list(scene.geometry.keys())[0]
                    tri_mesh = scene.geometry[mesh_name]
                    
                    # Convert to Open3D mesh
                    self.mesh = o3d.geometry.TriangleMesh()
                    self.mesh.vertices = o3d.utility.Vector3dVector(tri_mesh.vertices)
                    self.mesh.triangles = o3d.utility.Vector3iVector(tri_mesh.faces)
                    
                    # Preserve colors if available
                    if hasattr(tri_mesh.visual, 'vertex_colors') and len(tri_mesh.visual.vertex_colors) > 0:
                        colors = tri_mesh.visual.vertex_colors[:, :3] / 255.0  # Normalize to [0,1]
                        self.mesh.vertex_colors = o3d.utility.Vector3dVector(colors)
                        print(f"✅ Loaded GLB with {len(colors)} vertex colors")
                    elif hasattr(tri_mesh.visual, 'face_colors') and len(tri_mesh.visual.face_colors) > 0:
                        # Convert face colors to vertex colors (approximate)
                        print("Converting face colors to vertex colors...")
                        face_colors = tri_mesh.visual.face_colors[:, :3] / 255.0
                        vertex_colors = np.zeros((len(tri_mesh.vertices), 3))
                        for i, face in enumerate(tri_mesh.faces):
                            for vertex_idx in face:
                                vertex_colors[vertex_idx] = face_colors[i]
                        self.mesh.vertex_colors = o3d.utility.Vector3dVector(vertex_colors)
                        print(f"✅ Converted {len(face_colors)} face colors to vertex colors")
                    else:
                        print("⚠️ GLB file has no color information, using default")
                        # Apply a default color for GLB files without colors
                        self.mesh.paint_uniform_color([0.7, 0.7, 0.9])  # Light blue-gray
                else:
                    # Fallback to Open3D if trimesh fails
                    print("Trimesh failed, falling back to Open3D...")
                    self.mesh = o3d.io.read_triangle_mesh(self.mesh_path)
                    if not self.mesh.has_vertex_colors():
                        self.mesh.paint_uniform_color([0.7, 0.7, 0.9])
            else:
                # Use Open3D for other formats (STL, PLY, OBJ, etc.)
                self.mesh = o3d.io.read_triangle_mesh(self.mesh_path)
                
            # Validate mesh
            if len(self.mesh.vertices) == 0:
                raise ValueError(f"No vertices found in mesh file: {self.mesh_path}")
                
            print(f"Loaded mesh from: {self.mesh_path}")
            print(f"File format: {file_ext.upper()}")
            print(f"Vertices: {len(self.mesh.vertices)}, Triangles: {len(self.mesh.triangles)}")
            
            if len(self.mesh.vertex_colors) > 0:
                print(f"✅ Mesh has vertex colors: {len(self.mesh.vertex_colors)}")
            else:
                print("⚠️ Mesh has no vertex colors")
                
        except Exception as e:
            print(f"❌ Error loading mesh from {self.mesh_path}: {e}")
            self.mesh = None
    
    def visualize_as_point_cloud(self, num_points=100000):
        """Visualize mesh as point cloud"""
        if self.mesh is None:
            print("No mesh loaded")
            return
        
        pcd = self.mesh.sample_points_uniformly(number_of_points=num_points)
        print(f"Point cloud with {len(pcd.points)} points")
        
        # Use visualizer instead of draw_geometries for better stability
        vis = o3d.visualization.Visualizer()
        vis.create_window("Point Cloud Viewer")
        vis.add_geometry(pcd)
        vis.run()
        vis.destroy_window()
    
    def visualize_mesh(self, width=2400, height=1600):
        """Visualize mesh with simple lighting (macOS safe)"""
        if self.mesh is None:
            print("No mesh loaded")
            return
        
        # Compute normals for proper lighting
        self.mesh.compute_vertex_normals()
        
        # Use visualizer instead of draw_geometries for better stability
        vis = o3d.visualization.Visualizer()
        vis.create_window("Mesh Viewer", width=width, height=height)
        vis.add_geometry(self.mesh)
        
        # Setup render options for better color display
        render_option = vis.get_render_option()
        render_option.light_on = True
        render_option.mesh_show_wireframe = False
        if self.mesh.has_vertex_colors():
            render_option.mesh_color_option = o3d.visualization.MeshColorOption.Color
            print("✅ Using vertex colors for visualization")
        else:
            render_option.mesh_color_option = o3d.visualization.MeshColorOption.Default
            print("⚠️ No vertex colors found, using default shading")
        
        vis.run()
        vis.destroy_window()
        
    def visualize_mesh_with_bboxes_overlayed(self, bboxes, width=2400, height=1600, line_thickness=0.005):
        """Visualize mesh with bounding boxes overlayed
        
        Args:
            bboxes: List of bounding box dictionaries
            width: Window width
            height: Window height
            line_thickness: Thickness of bounding box lines (0.001-0.01 recommended)
        """
        if self.mesh is None:
            print("No mesh loaded")
            return
        
        # Compute normals for proper lighting
        self.mesh.compute_vertex_normals()
        
        # Set mesh color to light gray
        self.mesh.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray color
        
        # Use visualizer instead of draw_geometries for better stability
        vis = o3d.visualization.Visualizer()
        vis.create_window("Mesh Viewer with BBoxes", width=width, height=height)
        vis.add_geometry(self.mesh)
        
        # Add bounding boxes to visualization
        bbox_count = 0
        for i, bbox in enumerate(bboxes):
            min_bound = bbox['min_bound']
            max_bound = bbox['max_bound']
            
            # Validate bounding box data before creating geometry
            if min_bound is None or max_bound is None:
                print(f"Skipping bounding box {i}: bounds are None")
                continue
                
            if len(min_bound) != 3 or len(max_bound) != 3:
                print(f"Skipping bounding box {i}: invalid dimensions")
                continue
            
            min_bound = np.array(min_bound, dtype=np.float64)
            max_bound = np.array(max_bound, dtype=np.float64)
            
            # Check for valid bounds
            if np.any(min_bound >= max_bound):
                print(f"Skipping bounding box {i}: min_bound >= max_bound")
                continue
                
            # Create thick bounding box lines
            try:
                # Use thick cylinder-based lines for better visibility
                thick_lines = self.create_thick_bbox_lines(
                    min_bound, max_bound, 
                    [1, 0, 0],  # Red color
                    line_thickness
                )
                
                for line_cylinder in thick_lines:
                    vis.add_geometry(line_cylinder)
                
                bbox_count += 1
            except Exception as e:
                print(f"Failed to create bounding box {i}: {e}")

        print(f"Successfully added {bbox_count} bounding boxes to visualization")
        
        # Adjust camera view to see both mesh and bboxes
        vis.run()
        vis.destroy_window()

    def visualize_mesh_with_annotations_overlayed(self, annotations, width=2400, height=1600, show_text_labels=True, line_thickness=0.005):
        """Visualize mesh with annotation bounding boxes overlayed
        
        Args:
            annotations: List of annotation dictionaries
            width: Window width
            height: Window height
            show_text_labels: Whether to display text labels above bounding boxes
            line_thickness: Thickness of bounding box lines (0.001-0.01 recommended)
        """
        if self.mesh is None:
            print("No mesh loaded")
            return
        
        # Compute normals for proper lighting
        self.mesh.compute_vertex_normals()
        
        # Only set mesh color to light gray if it doesn't have vertex colors
        if not self.mesh.has_vertex_colors():
            self.mesh.paint_uniform_color([0.8, 0.8, 0.8])  # Light gray color
            print("Applied default gray color to mesh (no vertex colors found)")
        else:
            print("Preserving existing vertex colors")
        
        # Use visualizer instead of draw_geometries for better stability
        vis = o3d.visualization.Visualizer()
        vis.create_window("Mesh Viewer with Annotations", width=width, height=height)
        vis.add_geometry(self.mesh)
        
        # Setup render options for better color display
        render_option = vis.get_render_option()
        render_option.light_on = True
        render_option.mesh_show_wireframe = False
        if self.mesh.has_vertex_colors():
            render_option.mesh_color_option = o3d.visualization.MeshColorOption.Color
        else:
            render_option.mesh_color_option = o3d.visualization.MeshColorOption.Default
        
        # Color mapping for different annotation types
        color_map = {
            'plane': (0, 1, 0),     # Green for planes
            'cluster': (1, 0, 0),   # Red for clusters
            'object': (0, 0, 1),    # Blue for objects
            'default': (1, 1, 0)    # Yellow for unknown types
        }
        
        # Add bounding boxes to visualization
        bbox_count = 0
        for annotation in annotations:
            min_bound = annotation['min_bound']
            max_bound = annotation['max_bound']
            annotation_type = annotation.get('annotation_type', 'default')
            label = annotation.get('label', 'unknown')
            
            # Validate bounding box data before creating geometry
            if min_bound is None or max_bound is None:
                print(f"Skipping annotation {label}: bounds are None")
                continue
                
            if len(min_bound) != 3 or len(max_bound) != 3:
                print(f"Skipping annotation {label}: invalid dimensions")
                continue
            
            min_bound = np.array(min_bound, dtype=np.float64)
            max_bound = np.array(max_bound, dtype=np.float64)
            
            # Check for valid bounds
            if np.any(min_bound >= max_bound):
                print(f"Skipping annotation {label}: min_bound >= max_bound")
                continue
                
            # Create thick bounding box lines
            try:
                # Use thick cylinder-based lines for better visibility
                thick_lines = self.create_thick_bbox_lines(
                    min_bound, max_bound, 
                    color_map.get(annotation_type, color_map['default']),
                    line_thickness
                )
                
                for line_cylinder in thick_lines:
                    vis.add_geometry(line_cylinder)
                
                bbox_count += 1
                
            except Exception as e:
                print(f"Failed to create bounding box for {label}: {e}")

        print(f"Successfully added {bbox_count} annotation bounding boxes to visualization")
        
        # Adjust camera view to see both mesh and bboxes
        vis.run()
        vis.destroy_window()

    def export_mesh(self, output_path, file_format="ply"):
        """Export mesh to different formats
        
        Args:
            output_path (str): Path to save the exported mesh
            file_format (str): Format to export ('ply', 'obj', 'stl', 'glb')
        """
        if self.mesh is None:
            print("No mesh loaded")
            return False
        
        # Ensure mesh has normals for export
        self.mesh.compute_vertex_normals()
        
        try:
            if file_format.lower() in ["ply", "obj", "stl"]:
                success = o3d.io.write_triangle_mesh(output_path, self.mesh)
            elif file_format.lower() == "glb":
                # For GLB export, use trimesh to preserve colors better
                try:
                    # Convert to trimesh
                    vertices = np.asarray(self.mesh.vertices)
                    faces = np.asarray(self.mesh.triangles)
                    tri_mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
                    
                    # Add vertex colors if available
                    if self.mesh.has_vertex_colors():
                        colors = np.asarray(self.mesh.vertex_colors) * 255  # Convert back to 0-255
                        tri_mesh.visual.vertex_colors = colors.astype(np.uint8)
                    
                    # Export using trimesh
                    tri_mesh.export(output_path)
                    success = True
                    print(f"Exported GLB with colors using Trimesh")
                except Exception as e:
                    print(f"Trimesh GLB export failed, falling back to Open3D: {e}")
                    success = o3d.io.write_triangle_mesh(output_path, self.mesh)
            else:
                print(f"Unsupported format: {file_format}")
                return False
            
            if success:
                print(f"Mesh exported successfully to: {output_path}")
                return True
            else:
                print(f"Failed to export mesh to: {output_path}")
                return False
                
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def get_mesh_stats(self):
        """Get mesh dimensions (bounding box)"""
        if self.mesh is None:
            print("No mesh loaded")
            return None

        # Convert to Trimesh for bounds
        self.tri_mesh = trimesh.Trimesh(vertices=np.asarray(self.mesh.vertices),
                                        faces=np.asarray(self.mesh.triangles))
        bounds = self.tri_mesh.bounds  # shape (2, 3): [min, max]
        dimensions = bounds[1] - bounds[0]

        stats = {
            "min_bound": bounds[0].tolist(),
            "max_bound": bounds[1].tolist(),
            "dimensions": dimensions.tolist()
        }

        print(f"Mesh Dimensions:")
        print(f"  Min Bound: {stats['min_bound']}")
        print(f"  Max Bound: {stats['max_bound']}")
        print(f"  Dimensions (x, y, z): {stats['dimensions']}")

        return stats
    
    def create_thick_bbox_lines(self, min_bound, max_bound, color, line_thickness=0.005):
        """Create thick bounding box lines using cylinder geometries
        
        Args:
            min_bound: Minimum bounds [x, y, z]
            max_bound: Maximum bounds [x, y, z]
            color: RGB color tuple
            line_thickness: Thickness of the lines (radius of cylinders)
        
        Returns:
            List of cylinder geometries representing thick bbox lines
        """
        min_bound = np.array(min_bound)
        max_bound = np.array(max_bound)
        
        # Define the 8 corners of the bounding box
        corners = np.array([
            [min_bound[0], min_bound[1], min_bound[2]],  # 0
            [max_bound[0], min_bound[1], min_bound[2]],  # 1
            [max_bound[0], max_bound[1], min_bound[2]],  # 2
            [min_bound[0], max_bound[1], min_bound[2]],  # 3
            [min_bound[0], min_bound[1], max_bound[2]],  # 4
            [max_bound[0], min_bound[1], max_bound[2]],  # 5
            [max_bound[0], max_bound[1], max_bound[2]],  # 6
            [min_bound[0], max_bound[1], max_bound[2]]   # 7
        ])
        
        # Define the 12 edges of the bounding box
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Bottom face
            (4, 5), (5, 6), (6, 7), (7, 4),  # Top face
            (0, 4), (1, 5), (2, 6), (3, 7)   # Vertical edges
        ]
        
        cylinders = []
        for start_idx, end_idx in edges:
            start_point = corners[start_idx]
            end_point = corners[end_idx]
            
            # Calculate cylinder parameters
            direction = end_point - start_point
            length = np.linalg.norm(direction)
            
            if length > 0:
                # Create cylinder
                cylinder = o3d.geometry.TriangleMesh.create_cylinder(
                    radius=line_thickness, 
                    height=length,
                    resolution=8
                )
                
                # Position and orient the cylinder
                center = (start_point + end_point) / 2
                
                # Calculate rotation to align cylinder with edge direction
                direction_normalized = direction / length
                z_axis = np.array([0, 0, 1])
                
                # If direction is not parallel to z-axis, rotate
                if not np.allclose(direction_normalized, z_axis) and not np.allclose(direction_normalized, -z_axis):
                    rotation_axis = np.cross(z_axis, direction_normalized)
                    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)
                    rotation_angle = np.arccos(np.dot(z_axis, direction_normalized))
                    
                    # Create rotation matrix
                    cos_angle = np.cos(rotation_angle)
                    sin_angle = np.sin(rotation_angle)
                    ux, uy, uz = rotation_axis
                    
                    rotation_matrix = np.array([
                        [cos_angle + ux**2 * (1 - cos_angle), 
                         ux * uy * (1 - cos_angle) - uz * sin_angle,
                         ux * uz * (1 - cos_angle) + uy * sin_angle],
                        [uy * ux * (1 - cos_angle) + uz * sin_angle,
                         cos_angle + uy**2 * (1 - cos_angle),
                         uy * uz * (1 - cos_angle) - ux * sin_angle],
                        [uz * ux * (1 - cos_angle) - uy * sin_angle,
                         uz * uy * (1 - cos_angle) + ux * sin_angle,
                         cos_angle + uz**2 * (1 - cos_angle)]
                    ])
                    
                    cylinder.rotate(rotation_matrix, center=[0, 0, 0])
                elif np.allclose(direction_normalized, -z_axis):
                    # Flip if pointing in negative z direction
                    cylinder.rotate(cylinder.get_rotation_matrix_from_xyz([np.pi, 0, 0]), center=[0, 0, 0])
                
                cylinder.translate(center)
                cylinder.paint_uniform_color(color)
                cylinders.append(cylinder)
        
        return cylinders

# Usage example
if __name__ == "__main__":
    # Create processor instance with the available STL file from data directory
    processor = MeshProcessor("../data/bed.stl")
    
    # Get mesh statistics
    stats = processor.get_mesh_stats()
    
    # Only visualize if the mesh loaded successfully
    if stats is not None:
        # Try to load annotation format from data directory
        annotation_file = "../data/annotations/object_annotations.json"
        if os.path.exists(annotation_file):
            with open(annotation_file, 'r') as f:
                annotation_data = json.load(f)
            
            annotations = annotation_data.get('annotations', [])
            # Debug: Check the annotation data
            print(f"Found {len(annotations)} annotations")
            for annotation in annotations:
                print(f"Annotation: {annotation.get('annotation_type')} - {annotation.get('label')}")
                
            processor.visualize_mesh_with_annotations_overlayed(annotations)
        else:
            print(f"Annotation file not found: {annotation_file}")
            print("Run model_analysis.py first to generate annotations")
    else:
        print("Mesh failed to load or has no vertices - skipping visualization")


