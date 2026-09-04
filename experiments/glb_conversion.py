import trimesh
import sys
import argparse

def stl_to_glb(input_stl_path, output_glb_path):
    mesh = trimesh.load(input_stl_path)
    mesh.export(output_glb_path, file_type='glb')

def ply_to_glb(input_ply_path, output_glb_path):
    mesh = trimesh.load(input_ply_path)
    mesh.export(output_glb_path, file_type='glb')

if __name__ == "__main__":
    # input_stl = "room.stl"
    # output_glb = "toiletries.glb"
    # stl_to_glb(input_stl, output_glb)

    input_ply = "../data/bed.ply"
    output_glb = "../data/bed.glb"
    ply_to_glb(input_ply, output_glb)