import open3d as o3d

# Load and visualize
pcd = o3d.io.read_point_cloud("Yishun.ply")
print(pcd)
# See if colors are present
if pcd.has_colors():
    print("This PLY has RGB colors")
else:
    print("No colors found in PLY")

o3d.visualization.draw_geometries([pcd])

