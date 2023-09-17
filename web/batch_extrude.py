import os
import numpy as np
import trimesh

def extrude_trimesh_dxf_to_stl(input_folder, output_folder, extrusion_height=3.0):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".dxf"):
            dxf_path = os.path.join(input_folder, filename)
            mesh = trimesh.load(dxf_path)
            
            # Extract the 2D polygons from the 3D mesh
            polygons = mesh.polygons_full
            
            # Define the translation matrix for extrusion
            translation_matrix = np.eye(4)
            translation_matrix[2, 3] = extrusion_height
            
            # Extrude each polygon individually
            extruded_meshes = []
            for polygon in polygons:
                extruded_mesh = trimesh.creation.extrude_polygon(polygon, extrusion_height, transform=None)
                extruded_meshes.append(extruded_mesh)
            
            # Merge the extruded meshes into a single mesh
            combined_mesh = trimesh.util.concatenate(extruded_meshes)
            
            # Save the extruded mesh as STL
            stl_filename = filename.replace(".dxf", "_extruded.stl")
            stl_path = os.path.join(output_folder, stl_filename)
            combined_mesh.export(stl_path, file_type="stl")
import re
def extract_numeric_prefix(filename):
    match = re.match(r'slice_(\d+)_extruded\.stl', filename)
    return int(match.group(1)) if match else 0

def move_mesh(mesh, translation_vector):
    new_mesh = mesh.copy()  # Create a copy to avoid modifying the original mesh
    new_mesh.apply_translation(translation_vector)
    return new_mesh
def remove_duplicate_vertices(mesh):
    # Remove duplicate vertices from the mesh
    mesh.vertices, unique_indices = trimesh.grouping.unique_rows(mesh.vertices)
    mesh.faces = unique_indices[mesh.faces]
    return mesh

def compute_vertex_normals(mesh):
    # Compute vertex normals for the mesh
    mesh.compute_normals()
    return mesh

# if __name__ == "__main__":
    # height = 3.0
    # input_folder = "output_layers2"
    # output_folder = "output_stl_folder"
    # output_path = "combined_output.stl"
    
    
    
    
def combine_stl_files(input_folder, output_path, extrusion_height=3.0):
    meshes = []
    stls = []
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".stl"):
            stls.append(filename)
    
    names_of_stls = sorted(stls, key=extract_numeric_prefix)
    
    translation_vector = [0, 0, extrusion_height]  # Use the provided extrusion height
    cumulative_translation = [0, 0, 0]

    for index, name in enumerate(names_of_stls):
        stl_path = os.path.join(input_folder, name)
        mesh = trimesh.load(stl_path)
        
        # Calculate the translation for the current mesh
        mesh_translation = [coord + cum_trans for coord, cum_trans in zip(translation_vector, cumulative_translation)]
        
        # Apply the translation to the current mesh
        moved_mesh = move_mesh(mesh, mesh_translation)
        
        # Append the translated mesh to the list
        meshes.append(moved_mesh)
        
        # Update the cumulative translation for the next mesh
        cumulative_translation = mesh_translation
    
    combined_vertices = []
    combined_faces = []

    # Loop through each mesh and update the vertices and faces
    vertex_offset = 0
    for mesh in meshes:
        combined_vertices.extend(mesh.vertices.tolist())
        combined_faces.extend((mesh.faces + vertex_offset).tolist())
        vertex_offset += len(mesh.vertices)

    # Create the combined mesh
    combined_mesh = trimesh.Trimesh(vertices=combined_vertices, faces=combined_faces)

    # Optional: Clean up the mesh if needed


    # Save the combined mesh
    combined_mesh.export(output_path, file_type="stl")
# extrude_trimesh_dxf_to_stl(input_folder, output_folder,3.0)
# combine_stl_files(output_folder, output_path,3.0)