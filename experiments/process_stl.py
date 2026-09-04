#!/usr/bin/env python3
"""
STL Processing Pipeline for GroundBreaker

This is your main script for processing new STL files.
Run this script whenever you have a new STL file to analyze.

Usage:
    python process_stl.py <path_to_stl_file> [options]

Example:
    python process_stl.py ../data/room.stl
    python process_stl.py toiletries.stl --visualize --export-glb
"""

import argparse
import os
import sys
from pathlib import Path

# Import your processing modules
from scan_parser import MeshProcessor
from object_clustering import analyze_object_clusters
from glb_conversion import stl_to_glb
from overhead_view import create_overhead_view, extract_xz_bounds, load_annotations


def process_stl_file(stl_path, 
                    output_dir="output",
                    visualize=False,
                    export_glb=False,
                    generate_overhead=False,
                    clustering_eps=0.1,
                    clustering_min_samples=20,
                    custom_model_path=None):
    """
    Complete STL processing pipeline
    
    Args:
        stl_path: Path to STL file
        output_dir: Directory for output files
        visualize: Whether to show 3D visualization
        export_glb: Whether to export GLB format
        generate_overhead: Whether to generate 2D overhead view image
        clustering_eps: DBSCAN epsilon parameter
        clustering_min_samples: DBSCAN min_samples parameter
        custom_model_path: Custom path to model file for visualization (GLB, PLY, etc.)
    """
    
    print("="*60)
    print(f"PROCESSING STL FILE: {stl_path}")
    print("="*60)
    
    # Validate input file
    if not os.path.exists(stl_path):
        print(f"❌ Error: STL file not found: {stl_path}")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    annotations_dir = os.path.join(output_dir, "annotations")
    os.makedirs(annotations_dir, exist_ok=True)
    
    # Get base filename for outputs
    base_name = Path(stl_path).stem
    
    try:
        # Step 1: Load and validate mesh
        print("\n📁 STEP 1: Loading STL mesh...")
        processor = MeshProcessor(stl_path)
        
        # Step 2: Object clustering with 2D floor plane
        print("\n🎯 STEP 2: Object clustering with 2D floor plane...")
        num_clusters, final_clusters, floor_bounds = analyze_object_clusters(
            mesh_path=stl_path,
            scale_factor=1.0,
            eps=clustering_eps,
            min_samples=clustering_min_samples,
            annotation_folder=annotations_dir,
            output_suffix="2d_floor_clusters",
            use_filters=True,
            verbose=True
        )
        
        # Step 3: Generate 2D overhead view if requested
        if generate_overhead:
            print("\n🗺️ STEP 3: Generating 2D overhead view...")
            annotation_path = os.path.join(annotations_dir, f"{base_name}_2d_floor_clusters.json")
            
            if os.path.exists(annotation_path):
                # Load annotations and extract X-Z bounds
                annotations = load_annotations(annotation_path)
                xz_boxes, labels, floor_plane = extract_xz_bounds(annotations)
                
                if xz_boxes:
                    # Generate overhead view image
                    overhead_path = os.path.join(output_dir, f"{base_name}_overhead_view.png")
                    success = create_overhead_view(
                        xz_boxes, 
                        floor_plane=floor_plane,
                        output_path=overhead_path,
                        image_size=(12, 10),
                        dpi=300,
                        show_labels=True,
                        grid=True,
                        title=f"{base_name.title()} - Floor Plan",
                        n_areas=5,  # Group into 5 main areas
                        neighbor_distance_threshold=2.0,  # Objects within 2 units are neighbors
                        label_areas_only=True  # Only label main areas for cleaner view
                    )
                    if success:
                        print(f"✅ Overhead view saved to: {overhead_path}")
                    else:
                        print("❌ Failed to generate overhead view")
                else:
                    print("⚠️ No objects found for overhead view")
            else:
                print("⚠️ Annotations not found, skipping overhead view")
        
        # Step 4: Export GLB if requested
        if export_glb:
            print(f"\n💾 STEP {'4' if generate_overhead else '3'}: Exporting to GLB format...")
            glb_path = os.path.join(output_dir, f"{base_name}.glb")
            stl_to_glb(stl_path, glb_path)
            print(f"✅ GLB exported to: {glb_path}")
        
        # Step 5: Visualization if requested
        if visualize:
            step_num = 3 + (1 if generate_overhead else 0) + (1 if export_glb else 0)
            print(f"\n👁️ STEP {step_num}: Visualizing results...")
            
            # Determine which model file to use for visualization
            if custom_model_path:
                model_path = custom_model_path
                print(f"🎯 Using custom model file: {model_path}")
                if not os.path.exists(model_path):
                    print(f"❌ Custom model file not found: {model_path}")
                    return False
                # Create processor for custom model
                vis_processor = MeshProcessor(model_path)
            else:
                model_path = stl_path
                print(f"🎯 Using original STL file: {model_path}")
                vis_processor = processor  # Use already loaded processor
            
            # Use auto-generated annotation file (based on original STL name)
            annotation_path = os.path.join(annotations_dir, f"{base_name}_2d_floor_clusters.json")
            
            # Load annotations for visualization
            if os.path.exists(annotation_path):
                import json
                with open(annotation_path, 'r') as f:
                    annotation_data = json.load(f)
                annotations = annotation_data.get('annotations', [])
                print(f"Visualizing with {len(annotations)} annotations from: {annotation_path}")
                vis_processor.visualize_mesh_with_annotations_overlayed(annotations, line_thickness=0.02)
            else:
                print(f"⚠️ Annotation file not found: {annotation_path}")
                print("Showing basic mesh without annotations")
                vis_processor.visualize_mesh()
        
        # Summary
        print("\n" + "="*60)
        print("✅ PROCESSING COMPLETE")
        print("="*60)
        print(f"📄 Input: {stl_path}")
        print(f"📁 Output directory: {output_dir}")
        print(f"🎯 Clusters found: {num_clusters}")
        print(f"🎯 Clusters after filtering: {final_clusters}")
        if num_clusters > 0:
            success_rate = (final_clusters / num_clusters) * 100
            print(f"🎯 Success rate: {success_rate:.1f}%")
        
        # List output files
        print(f"\n📄 Generated files:")
        annotation_file = f"{base_name}_2d_floor_clusters.json"
        print(f"  - {os.path.join(annotations_dir, annotation_file)}")
        if generate_overhead:
            overhead_file = f"{base_name}_overhead_view.png"
            print(f"  - {os.path.join(output_dir, overhead_file)}")
        if export_glb:
            print(f"  - {os.path.join(output_dir, f'{base_name}.glb')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with command line interface"""
    
    parser = argparse.ArgumentParser(
        description="Process STL files for object detection and clustering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_stl.py room.stl
  python process_stl.py ../data/toiletries.stl --visualize
  python process_stl.py room.stl --export-glb --output-dir results
  python process_stl.py room.stl --overhead-view --visualize
  python process_stl.py room.stl --eps 0.05 --min-samples 30 --overhead-view
  
  # Apply STL annotations to a different model format:
  python process_stl.py room.stl --visualize --model-file room.glb
  python process_stl.py room.stl --visualize --model-file room.ply
  
  # Process STL but visualize with different model:
  python process_stl.py room.stl --export-glb --visualize --model-file room_cleaned.ply
        """
    )
    
    # Required arguments
    parser.add_argument('stl_file', 
                       help='Path to the STL file to process')
    
    # Optional arguments
    parser.add_argument('--output-dir', '-o',
                       default='output',
                       help='Output directory for results (default: output)')
    
    parser.add_argument('--visualize', '-v',
                       action='store_true',
                       help='Show 3D visualization of results')
    
    parser.add_argument('--export-glb', '-g',
                       action='store_true',
                       help='Export mesh to GLB format')
    
    parser.add_argument('--overhead-view', '-oh',
                       action='store_true',
                       help='Generate 2D overhead view image')
    
    parser.add_argument('--eps',
                       type=float,
                       default=0.1,
                       help='DBSCAN epsilon parameter (default: 0.1)')
    
    parser.add_argument('--min-samples',
                       type=int,
                       default=20,
                       help='DBSCAN min_samples parameter (default: 20)')
    
    parser.add_argument('--model-file', '-m',
                       help='Custom path to model file for visualization (GLB, PLY, STL, etc.)')

    args = parser.parse_args()
    
    # Validate custom model file if provided
    if args.model_file and not os.path.exists(args.model_file):
        print(f"❌ Error: Custom model file not found: {args.model_file}")
        sys.exit(1)
    
    # Process the file
    success = process_stl_file(
        stl_path=args.stl_file,
        output_dir=args.output_dir,
        visualize=args.visualize,
        export_glb=args.export_glb,
        generate_overhead=args.overhead_view,
        clustering_eps=args.eps,
        clustering_min_samples=args.min_samples,
        custom_model_path=args.model_file
    )
    
    if success:
        print("\n🎉 All done! Your STL has been processed successfully.")
    else:
        print("\n💥 Processing failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
