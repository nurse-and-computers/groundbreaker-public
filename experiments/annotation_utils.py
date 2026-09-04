import os
import json
import numpy as np


class BoundingBoxAnnotator:
    """A class for managing bounding box annotations for 3D objects"""
    
    def __init__(self):
        self.annotations = []
    
    def add_annotation(self, annotation_type, label, min_bound, max_bound, metadata=None):
        """Add a bounding box annotation
        
        Args:
            annotation_type (str): Type of annotation ('plane', 'cluster', 'object', etc.)
            label (str): Human-readable label for the annotation
            min_bound (np.array): Minimum bounds [x, y, z]
            max_bound (np.array): Maximum bounds [x, y, z]
            metadata (dict): Additional metadata about the annotation
        """
        annotation = {
            'annotation_type': annotation_type,
            'label': label,
            'min_bound': min_bound.tolist() if isinstance(min_bound, np.ndarray) else min_bound,
            'max_bound': max_bound.tolist() if isinstance(max_bound, np.ndarray) else max_bound,
            'metadata': metadata or {}
        }
        self.annotations.append(annotation)
    
    def add_plane_annotation(self, points, plane_model, label="floor_plane"):
        """Add a plane annotation with its bounding box"""
        if len(points) == 0:
            print(f"No points for plane {label}")
            return
            
        min_bound = points.min(axis=0)
        max_bound = points.max(axis=0)
        
        metadata = {
            'plane_equation': plane_model.tolist() if isinstance(plane_model, np.ndarray) else plane_model,
            'point_count': len(points)
        }
        
        self.add_annotation('plane', label, min_bound, max_bound, metadata)
    
    def add_cluster_annotation(self, points, cluster_id, scale_factor=1.0):
        """Add a cluster annotation with its bounding box"""
        if len(points) == 0:
            print(f"No points for cluster {cluster_id}")
            return
            
        min_bound = points.min(axis=0) * scale_factor
        max_bound = points.max(axis=0) * scale_factor
        
        metadata = {
            'cluster_id': cluster_id,
            'point_count': len(points),
            'scale_factor': scale_factor
        }
        
        label = f"cluster_{cluster_id}"
        self.add_annotation('cluster', label, min_bound, max_bound, metadata)
    
    def export_annotations(self, output_path):
        """Export all annotations to JSON file"""
        if not self.annotations:
            print("No annotations to export.")
            return
        
        # Create output directory if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        export_data = {
            'annotations': self.annotations,
            'total_count': len(self.annotations),
            'annotation_types': list(set(ann['annotation_type'] for ann in self.annotations))
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=4)
        print(f"Exported {len(self.annotations)} annotations to {output_path}")
    
    def get_annotations_by_type(self, annotation_type):
        """Get all annotations of a specific type"""
        return [ann for ann in self.annotations if ann['annotation_type'] == annotation_type]
    
    def clear_annotations(self):
        """Clear all annotations"""
        self.annotations = []
        print("Cleared all annotations")
