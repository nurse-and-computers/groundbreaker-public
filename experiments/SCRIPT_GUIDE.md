# GroundBreaker Backend - Script Overview

This guide explains what each Python script does and how to use them when processing new STL files.

## 🚀 Quick Start - Processing a New STL

**For most cases, you only need one command:**

```bash
python process_stl.py your_file.stl --visualize
```

This will run the complete pipeline and show you the results.

## 📋 Script Breakdown

### 🎯 Main Processing Scripts

#### `process_stl.py` - **MAIN PIPELINE** ⭐
**This is your go-to script for new STL files**
- **Purpose**: Complete STL processing pipeline
- **What it does**: 
  - Loads STL file
  - Detects floor plane using 2D approach
  - Clusters objects using DBSCAN
  - Filters clusters for quality
  - Exports annotations
  - Optional visualization and GLB export
- **Usage**: 
  ```bash
  python process_stl.py room.stl --visualize
  python process_stl.py toiletries.stl --export-glb
  ```

#### `object_clustering.py` - **Core Clustering Engine**
- **Purpose**: Object detection and clustering with 2D floor plane filtering
- **What it does**:
  - Creates 2D floor plane from mesh bounds
  - Performs DBSCAN clustering
  - Filters clusters based on size, shape, density
  - Applies X-Z overlap filtering with floor area
- **Usage**: Can be run standalone or imported
  ```bash
  python object_clustering.py  # Uses room.stl by default
  ```

### 🔧 Utility Scripts

#### `scan_parser.py` - **Mesh Loading & Visualization**
- **Purpose**: STL/PLY mesh loading and basic visualization
- **Key class**: `MeshProcessor`
- **What it does**:
  - Loads mesh files safely
  - Provides visualization methods
  - Handles mesh format conversions
- **Usage**: Usually imported by other scripts

#### `floor_plane.py` - **Floor Detection**
- **Purpose**: Advanced 3D floor plane detection using RANSAC
- **What it does**:
  - Finds lowest horizontal plane in mesh
  - Quality assessment of plane candidates
  - Noise reduction and filtering
- **Usage**: Imported by clustering scripts

#### `annotation_utils.py` - **Annotation Management**
- **Purpose**: Creates and exports bounding box annotations
- **Key class**: `BoundingBoxAnnotator`
- **What it does**:
  - Manages object annotations
  - Exports to JSON format
  - Handles planes and clusters
- **Usage**: Imported by processing scripts

#### `glb_conversion.py` - **Format Conversion**
- **Purpose**: Convert STL/PLY to GLB format
- **What it does**:
  - STL → GLB conversion
  - PLY → GLB conversion
- **Usage**: 
  ```bash
  python glb_conversion.py  # Edit file to set paths
  ```

### 🧪 Development/Test Scripts

#### `model_analysis.py` - **Legacy Analysis**
- **Purpose**: Older analysis script for specific models
- **Status**: Replaced by `process_stl.py` for most use cases
- **Note**: Still works but uses older clustering approach

#### `ml.py` - **Point Cloud Utilities**
- **Purpose**: Basic point cloud loading and visualization
- **Status**: Development/testing script

### 🌐 Web Scripts

#### `app.py` - **Flask Web Server**
- **Purpose**: Basic web API (currently minimal)
- **Status**: Development placeholder

## 📁 Typical Workflow for New STL

### Option 1: Simple Processing (Recommended)
```bash
# Process STL with visualization
python process_stl.py your_file.stl --visualize

# Process with GLB export
python process_stl.py your_file.stl --visualize --export-glb
```

### Option 2: Custom Parameters
```bash
# Fine-tune clustering parameters
python process_stl.py room.stl --eps 0.05 --min-samples 30 --visualize

# Custom output directory
python process_stl.py room.stl --output-dir my_results --visualize
```

### Option 3: Manual Steps (Advanced)
```bash
# 1. Basic clustering only
python object_clustering.py

# 2. Convert to GLB separately
python glb_conversion.py  # Edit script to set file paths

# 3. Custom analysis
python model_analysis.py  # Edit script to set file path
```

## 📊 Output Files

After processing, you'll get:

```
output/
├── annotations/
│   └── your_file_2d_floor_clusters.json  # Object annotations
└── your_file.glb                         # GLB format (if requested)
```

## 🎛️ Key Parameters

- **`--eps`**: DBSCAN clustering distance (smaller = more clusters)
- **`--min-samples`**: Minimum points per cluster (larger = fewer, denser clusters)
- **`--visualize`**: Show 3D results
- **`--export-glb`**: Create GLB file for web viewing

## 🎯 Best Practices

1. **Start simple**: Use `process_stl.py` with default parameters
2. **Visualize first**: Always use `--visualize` to see results
3. **Adjust if needed**: Modify `--eps` and `--min-samples` for better clustering
4. **Check output**: Look at the annotations JSON for detected objects

## 🔍 Troubleshooting

- **No objects detected**: Try smaller `--eps` value (e.g., 0.05)
- **Too many tiny clusters**: Increase `--min-samples` (e.g., 30-50)
- **Visualization crashes**: Remove `--visualize` flag
- **File not found**: Use full path to STL file

## 🏆 Recommended Commands

```bash
# Most common usage
python process_stl.py room.stl --visualize

# For detailed room analysis
python process_stl.py room.stl --eps 0.05 --min-samples 30 --visualize --export-glb

# Quick processing without visualization
python process_stl.py toiletries.stl --export-glb
```
