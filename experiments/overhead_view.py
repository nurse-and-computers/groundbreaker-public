#!/usr/bin/env python3
"""
2D Overhead View Generator for GroundBreaker Annotations

This script takes 3D annotations and creates a 2D overhead view image
showing the X-Z bounding boxes of all detected objects.

Usage:
    python overhead_view.py <annotation_file> [options]

Example:
    python overhead_view.py output/annotations/room_2d_floor_clusters.json
    python overhead_view.py output/annotations/room_2d_floor_clusters.json --output room_overhead.png --scale 50
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import os
from pathlib import Path
import colorsys


def load_annotations(annotation_path):
    """Load annotations from JSON file"""
    with open(annotation_path, 'r') as f:
        data = json.load(f)
    return data.get('annotations', [])


def extract_xz_bounds(annotations):
    """Extract X-Z bounding boxes from 3D annotations"""
    xz_boxes = []
    labels = []
    floor_plane = None
    
    for ann in annotations:
        if ann.get('annotation_type') == 'cluster':
            min_bound = ann['min_bound']
            max_bound = ann['max_bound']
            
            # Extract X-Z bounds (ignore Y dimension)
            x_min, y_min, z_min = min_bound
            x_max, y_max, z_max = max_bound
            
            xz_box = {
                'x_min': x_min,
                'x_max': x_max,
                'z_min': z_min,
                'z_max': z_max,
                'width': x_max - x_min,
                'depth': z_max - z_min,
                'area': (x_max - x_min) * (z_max - z_min),
                'center_x': (x_min + x_max) / 2,
                'center_z': (z_min + z_max) / 2,
                'label': ann.get('label', 'object'),
                'metadata': ann.get('metadata', {})
            }
            
            xz_boxes.append(xz_box)
            labels.append(ann.get('label', f"Object {len(xz_boxes)}"))
            
        elif ann.get('annotation_type') == 'plane' and 'floor' in ann.get('label', '').lower():
            # Extract floor plane bounds
            min_bound = ann['min_bound']
            max_bound = ann['max_bound']
            
            floor_plane = {
                'x_min': min_bound[0],
                'x_max': max_bound[0],
                'z_min': min_bound[2],
                'z_max': max_bound[2],
                'width': max_bound[0] - min_bound[0],
                'depth': max_bound[2] - min_bound[2],
                'metadata': ann.get('metadata', {})
            }
    
    return xz_boxes, labels, floor_plane


def find_area_groups(xz_boxes, n_areas=5, neighbor_distance_threshold=2.0):
    """
    Group boxes into areas and their neighbors for floor plan visualization
    
    Args:
        xz_boxes: List of bounding box dictionaries
        n_areas: Number of largest boxes to consider as main areas
        neighbor_distance_threshold: Maximum distance to consider boxes as neighbors
        
    Returns:
        area_groups: List of dictionaries with area info and neighbors
        ungrouped_indices: List of indices for boxes not assigned to any area
    """
    if not xz_boxes:
        return [], []
    
    # Sort boxes by area (largest first)
    sorted_boxes = sorted(enumerate(xz_boxes), key=lambda x: x[1]['area'], reverse=True)
    
    # Select top N largest boxes as main areas
    main_areas = sorted_boxes[:min(n_areas, len(sorted_boxes))]
    remaining_boxes = sorted_boxes[n_areas:]
    
    print(f"📍 Selected {len(main_areas)} main areas from {len(xz_boxes)} total objects")
    
    area_groups = []
    used_neighbor_indices = set()
    
    for area_idx, (orig_idx, area_box) in enumerate(main_areas):
        # Find neighbors for this area
        neighbors = []
        area_center = np.array([area_box['center_x'], area_box['center_z']])
        
        for neighbor_idx, (neighbor_orig_idx, neighbor_box) in enumerate(remaining_boxes):
            if neighbor_orig_idx in used_neighbor_indices:
                continue  # Already assigned to another area
                
            neighbor_center = np.array([neighbor_box['center_x'], neighbor_box['center_z']])
            distance = np.linalg.norm(area_center - neighbor_center)
            
            # Check if neighbor is within area bounds (expanded by threshold)
            expanded_x_min = area_box['x_min'] - neighbor_distance_threshold
            expanded_x_max = area_box['x_max'] + neighbor_distance_threshold
            expanded_z_min = area_box['z_min'] - neighbor_distance_threshold
            expanded_z_max = area_box['z_max'] + neighbor_distance_threshold
            
            is_within_expanded = (
                neighbor_box['center_x'] >= expanded_x_min and
                neighbor_box['center_x'] <= expanded_x_max and
                neighbor_box['center_z'] >= expanded_z_min and
                neighbor_box['center_z'] <= expanded_z_max
            )
            
            is_close = distance <= neighbor_distance_threshold
            
            if is_within_expanded or is_close:
                neighbors.append({
                    'box': neighbor_box,
                    'original_index': neighbor_orig_idx,
                    'distance': distance
                })
                used_neighbor_indices.add(neighbor_orig_idx)
        
        # Sort neighbors by distance (closest first)
        neighbors.sort(key=lambda x: x['distance'])
        
        area_group = {
            'area_box': area_box,
            'area_index': orig_idx,
            'group_id': area_idx,
            'neighbors': neighbors,
            'base_color_index': area_idx
        }
        
        area_groups.append(area_group)
        
        print(f"  Area {area_idx + 1}: {area_box['area']:.1f} sq units, {len(neighbors)} neighbors")
    
    # Handle ungrouped boxes (not main areas and not neighbors)
    used_main_indices = set([group['area_index'] for group in area_groups])
    ungrouped_indices = []
    for i, box in enumerate(xz_boxes):
        if i not in used_main_indices and i not in used_neighbor_indices:
            ungrouped_indices.append(i)
    
    if ungrouped_indices:
        print(f"  {len(ungrouped_indices)} ungrouped objects will use neutral colors")
    
    return area_groups, ungrouped_indices


def generate_area_colors(n_areas):
    """Generate distinct base colors for areas using HSV color space"""
    colors = []
    for i in range(n_areas):
        # Distribute hues evenly around color wheel
        hue = i / n_areas
        # Use high saturation and medium brightness for main areas
        saturation = 0.8
        value = 0.9
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        colors.append(rgb)
    return colors


def darken_color(rgb_color, factor=0.6):
    """Darken an RGB color by reducing its brightness"""
    return tuple(c * factor for c in rgb_color)


def create_overhead_view(xz_boxes, floor_plane=None, output_path="overhead_view.png", 
                        image_size=(12, 10), dpi=300, show_labels=True,
                        grid=True, title=None, n_areas=5, neighbor_distance_threshold=2.0,
                        label_areas_only=False):
    """Create 2D overhead view image with area-based coloring for floor plan visualization"""
    
    if not xz_boxes:
        print("❌ No cluster annotations found to visualize")
        return False
    
    # Group boxes into areas and neighbors
    area_groups, ungrouped_indices = find_area_groups(xz_boxes, n_areas, neighbor_distance_threshold)
    
    # Generate base colors for areas
    base_colors = generate_area_colors(len(area_groups))
    
    # Calculate overall bounds including floor plane
    all_x_coords = []
    all_z_coords = []
    
    for box in xz_boxes:
        all_x_coords.extend([box['x_min'], box['x_max']])
        all_z_coords.extend([box['z_min'], box['z_max']])
    
    # Include floor plane in bounds calculation if available
    if floor_plane:
        all_x_coords.extend([floor_plane['x_min'], floor_plane['x_max']])
        all_z_coords.extend([floor_plane['z_min'], floor_plane['z_max']])
    
    x_min_global = min(all_x_coords)
    x_max_global = max(all_x_coords)
    z_min_global = min(all_z_coords)
    z_max_global = max(all_z_coords)
    
    # Add padding (10% of range)
    x_range = x_max_global - x_min_global
    z_range = z_max_global - z_min_global
    padding_x = x_range * 0.1
    padding_z = z_range * 0.1
    
    x_min_global -= padding_x
    x_max_global += padding_x
    z_min_global -= padding_z
    z_max_global += padding_z
    
    print(f"📐 Scene bounds: X[{x_min_global:.2f}, {x_max_global:.2f}], Z[{z_min_global:.2f}, {z_max_global:.2f}]")
    print(f"📏 Scene size: {x_range:.2f} x {z_range:.2f} units")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=image_size, dpi=dpi)
    
    # Set up the plot
    ax.set_xlim(x_min_global, x_max_global)
    ax.set_ylim(z_min_global, z_max_global)
    ax.set_aspect('equal')
    
    # Set title
    if title:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    else:
        ax.set_title(f'Floor Plan - {len(area_groups)} Areas, {len(xz_boxes)} Objects', 
                    fontsize=16, fontweight='bold', pad=20)
    
    # Labels and grid
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Z Coordinate', fontsize=12)
    
    if grid:
        ax.grid(True, alpha=0.2, linestyle='--')
    
    # Draw floor plane first as background if available
    if floor_plane:
        floor_rect = Rectangle(
            (floor_plane['x_min'], floor_plane['z_min']),
            floor_plane['width'],
            floor_plane['depth'],
            linewidth=2,
            edgecolor='darkgray',
            facecolor='lightgray',
            alpha=0.2,
            label='Floor Plane'
        )
        ax.add_patch(floor_rect)
        
        # Add floor plane label
        floor_center_x = floor_plane['x_min'] + floor_plane['width'] / 2
        floor_center_z = floor_plane['z_min'] + floor_plane['depth'] / 2
        ax.text(floor_center_x, floor_center_z, 'FLOOR', 
               ha='center', va='center', fontsize=12, fontweight='bold',
               color='darkgray', alpha=0.5)
    
    # Draw area groups
    for group_idx, group in enumerate(area_groups):
        base_color = base_colors[group_idx]
        dark_color = darken_color(base_color)
        
        # Draw main area box
        area_box = group['area_box']
        area_rect = Rectangle(
            (area_box['x_min'], area_box['z_min']),
            area_box['width'],
            area_box['depth'],
            linewidth=2,
            edgecolor='black',
            facecolor=base_color,
            alpha=0.8,
            label=f"Area {group_idx + 1}"
        )
        ax.add_patch(area_rect)
        
        # Add area label (always show for main areas)
        if show_labels or not label_areas_only:
            center_x = area_box['x_min'] + area_box['width'] / 2
            center_z = area_box['z_min'] + area_box['depth'] / 2
            
            # Area number with larger font
            ax.text(center_x, center_z, f"A{group_idx + 1}", 
                   ha='center', va='center', fontsize=12, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
        
        # Draw neighbor boxes with darker shade
        for neighbor in group['neighbors']:
            neighbor_box = neighbor['box']
            neighbor_rect = Rectangle(
                (neighbor_box['x_min'], neighbor_box['z_min']),
                neighbor_box['width'],
                neighbor_box['depth'],
                linewidth=1,
                edgecolor='black',
                facecolor=dark_color,
                alpha=0.7
            )
            ax.add_patch(neighbor_rect)
            
            # Only label neighbors if not in areas-only mode and they're significant size
            if show_labels and not label_areas_only and neighbor_box['area'] > 0.5:
                n_center_x = neighbor_box['x_min'] + neighbor_box['width'] / 2
                n_center_z = neighbor_box['z_min'] + neighbor_box['depth'] / 2
                ax.text(n_center_x, n_center_z, '•', 
                       ha='center', va='center', fontsize=8, fontweight='bold',
                       color='white')
    
    # Draw ungrouped boxes with neutral gray
    for idx in ungrouped_indices:
        box = xz_boxes[idx]
        ungrouped_rect = Rectangle(
            (box['x_min'], box['z_min']),
            box['width'],
            box['depth'],
            linewidth=1,
            edgecolor='gray',
            facecolor='lightgray',
            alpha=0.5
        )
        ax.add_patch(ungrouped_rect)
    
    # Add statistics text box
    stats_text = f"Areas: {len(area_groups)}\n"
    stats_text += f"Objects: {len(xz_boxes)}\n"
    if floor_plane:
        stats_text += f"Floor: {floor_plane['width']:.1f} × {floor_plane['depth']:.1f} units\n"
    stats_text += f"Scene: {x_range:.1f} × {z_range:.1f} units"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           verticalalignment='top', fontsize=10,
           bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    # Invert Y axis so that positive Z points "forward" (up in the image)
    ax.invert_yaxis()
    
    # Tight layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"✅ Overhead view saved to: {output_path}")
    print(f"📊 Image size: {image_size[0]}×{image_size[1]} inches at {dpi} DPI")
    
    plt.close()
    
    return True


def generate_object_summary(xz_boxes, output_dir):
    """Generate a text summary of detected objects"""
    summary_path = os.path.join(output_dir, "object_summary.txt")
    
    with open(summary_path, 'w') as f:
        f.write("OVERHEAD VIEW - OBJECT SUMMARY\n")
        f.write("="*50 + "\n\n")
        
        f.write(f"Total objects detected: {len(xz_boxes)}\n\n")
        
        # Calculate statistics
        widths = [box['width'] for box in xz_boxes]
        depths = [box['depth'] for box in xz_boxes]
        areas = [box['width'] * box['depth'] for box in xz_boxes]
        
        f.write("STATISTICS:\n")
        f.write(f"Average width: {np.mean(widths):.2f} units\n")
        f.write(f"Average depth: {np.mean(depths):.2f} units\n")
        f.write(f"Average area: {np.mean(areas):.2f} sq units\n")
        f.write(f"Largest object: {max(areas):.2f} sq units\n")
        f.write(f"Smallest object: {min(areas):.2f} sq units\n\n")
        
        f.write("OBJECT DETAILS:\n")
        f.write("-" * 30 + "\n")
        
        # Sort by area (largest first)
        sorted_boxes = sorted(enumerate(xz_boxes), key=lambda x: x[1]['width'] * x[1]['depth'], reverse=True)
        
        for i, (orig_idx, box) in enumerate(sorted_boxes):
            area = box['width'] * box['depth']
            f.write(f"Object {orig_idx+1}: {box['width']:.2f} × {box['depth']:.2f} units (area: {area:.2f})\n")
            f.write(f"  Position: X[{box['x_min']:.2f}, {box['x_max']:.2f}], Z[{box['z_min']:.2f}, {box['z_max']:.2f}]\n")
            
            # Add metadata if available
            if box['metadata']:
                point_count = box['metadata'].get('point_count', 'unknown')
                f.write(f"  Points: {point_count}\n")
            f.write("\n")
    
    print(f"📄 Object summary saved to: {summary_path}")
    return summary_path


def main():
    """Main entry point with command line interface"""
    
    parser = argparse.ArgumentParser(
        description="Generate 2D overhead view from 3D annotations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python overhead_view.py output/annotations/room_2d_floor_clusters.json
  python overhead_view.py output/annotations/room_2d_floor_clusters.json --output room_overhead.png
  python overhead_view.py output/annotations/room_2d_floor_clusters.json --size 16 12 --dpi 150
        """
    )
    
    # Required arguments
    parser.add_argument('annotation_file', 
                       help='Path to the annotation JSON file')
    
    # Optional arguments
    parser.add_argument('--output', '-o',
                       help='Output image path (default: auto-generated from input)')
    
    parser.add_argument('--size', nargs=2, type=float,
                       default=[12, 10],
                       help='Image size in inches: width height (default: 12 10)')
    
    parser.add_argument('--dpi', type=int,
                       default=300,
                       help='Image DPI/resolution (default: 300)')
    
    parser.add_argument('--no-labels',
                       action='store_true',
                       help='Hide object labels and dimensions')
    
    parser.add_argument('--no-grid',
                       action='store_true', 
                       help='Hide grid lines')
    
    parser.add_argument('--title',
                       help='Custom title for the image')
    
    parser.add_argument('--summary',
                       action='store_true',
                       help='Generate object summary text file')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.annotation_file):
        print(f"❌ Error: Annotation file not found: {args.annotation_file}")
        return False
    
    # Generate output filename if not provided
    if not args.output:
        input_path = Path(args.annotation_file)
        output_dir = input_path.parent
        base_name = input_path.stem.replace('_2d_floor_clusters', '')
        args.output = output_dir / f"{base_name}_overhead_view.png"
    
    print("="*60)
    print("GENERATING 2D OVERHEAD VIEW")
    print("="*60)
    print(f"📁 Input: {args.annotation_file}")
    print(f"🖼️ Output: {args.output}")
    
    try:
        # Load annotations
        print("\n📋 Loading annotations...")
        annotations = load_annotations(args.annotation_file)
        print(f"Found {len(annotations)} total annotations")
        
        # Extract X-Z bounds
        print("\n📐 Extracting X-Z bounding boxes...")
        xz_boxes, labels, floor_plane = extract_xz_bounds(annotations)
        print(f"Extracted {len(xz_boxes)} object bounding boxes")
        if floor_plane:
            print(f"Found floor plane: {floor_plane['width']:.2f} × {floor_plane['depth']:.2f} units")
        else:
            print("No floor plane found in annotations")
        
        if not xz_boxes:
            print("❌ No cluster annotations found in the file")
            return False
        
        # Create overhead view
        print(f"\n🎨 Creating overhead view image...")
        success = create_overhead_view(
            xz_boxes, 
            floor_plane=floor_plane,
            output_path=args.output,
            image_size=args.size,
            dpi=args.dpi,
            show_labels=not args.no_labels,
            grid=not args.no_grid,
            title=args.title
        )
        
        if not success:
            return False
        
        # Generate summary if requested
        if args.summary:
            print(f"\n📄 Generating object summary...")
            output_dir = Path(args.output).parent
            generate_object_summary(xz_boxes, output_dir)
        
        print("\n" + "="*60)
        print("✅ OVERHEAD VIEW GENERATION COMPLETE")
        print("="*60)
        print(f"🖼️ Image: {args.output}")
        print(f"📊 Objects visualized: {len(xz_boxes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Overhead view generated successfully!")
    else:
        print("\n💥 Failed to generate overhead view.")
        exit(1)
