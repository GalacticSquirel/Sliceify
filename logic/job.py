from imports import *

global progress
progress = 0

def update_progress(curr_progress: int, job_name: str) -> int:
    """
    Update the progress of a job and save it to a JSON file.

    Args:
        curr_progress (int): The current progress of the job.
        job_name (str): The name of the job.

    Returns:
        int: The updated progress of the job.
    """
    print(curr_progress)
    json.dump({'progress': curr_progress}, open(
        os.path.join('static', job_name, 'data.json'), "w"))
    return curr_progress


def initial_configuration(job_name: str, slice_height: float) -> str:
    """
    Generate the initial configuration for a job.

    Args:
        job_name (str): The name of the job.
        slice_height (float): The desired slice height.

    Returns:
        str: The rendered template for the configuration page.

    Raises:
        None

    Notes:
        - The function first constructs the path to the uploaded STL file based on the job name.
        - It then loads the mesh using `trimesh.load`.
        - If the mesh is not None and is of type `trimesh.base.Trimesh`, it proceeds to calculate the minimum and maximum z-coordinates of the mesh.
        - The function calculates the maximum and minimum slice heights based on the mesh bounds.
        - If the provided slice height exceeds the maximum slice height, it is adjusted to the maximum value.
        - Finally, the function renders the configuration template with the necessary variables and returns it as a string.

    """
    path = os.path.join('static', job_name, 'upload/upload.stl')
    mesh = trimesh.load(path)
    
    if mesh is not None:
        if type(mesh) == trimesh.base.Trimesh:
            min_z, max_z = mesh.bounds[:, 2]
            max_slice_height = (max_z - min_z) / 2
            min_slice_height = (max_z - min_z) / 5000
            if slice_height > max_slice_height:
                slice_height = max_slice_height
            # doesn't account for rotation
            print(min_slice_height, max_slice_height)
            return render_template('job/config.html', path=f'/static/{job_name}/upload/upload.stl', job_name=job_name, slice_height=slice_height, max_slice_height=max_slice_height, min_slice_height=min_slice_height)

    return str("Error: Failed to load mesh.")

def remake_if_exist(path: str) -> bool:
    """
    Remakes the specified directory if it exists, or creates a new directory if it does not exist.

    Parameters:
        path (str): The path of the directory to be remade or created.

    Returns:
        bool: True if the directory was remade, False if it was created.
    """
    if not os.path.exists(path):
        os.makedirs(path)
        return False
    else:
        
        shutil.rmtree(path)
        os.makedirs(path)
        return True

def extract_numeric_prefix(filename: str) -> int:
    """
    Extracts the numeric prefix from a given filename.

    Args:
        filename (str): The filename from which to extract the numeric prefix.

    Returns:
        int: The extracted numeric prefix as an integer. If no numeric prefix is found, returns 0.
    """
    match = re.match(r'slice_(\d+)_extruded\.stl', filename)
    return int(match.group(1)) if match else 0

def move_mesh(mesh: trimesh.base.Trimesh, translation_vector:list) -> trimesh.base.Trimesh:
    """
    Move a mesh by applying a translation vector.

    Parameters:
        mesh (trimesh.base.Trimesh): The mesh to be moved.
        translation_vector (list): The vector representing the translation to be applied.

    Returns:
        trimesh.base.Trimesh: The new moved mesh.
    """
    new_mesh = mesh.copy()  
    new_mesh.apply_translation(translation_vector)
    return new_mesh


def slice_stl_file(mesh: trimesh.base.Trimesh, job_name: str, slice_height: float, svg_directory: str, dxf_directory: str) -> list:
    """
    Generate a list of 2D slices from a 3D mesh file in STL format.

    Args:
        mesh (trimesh.base.Trimesh): The 3D mesh object to be sliced.
        job_name (str): The name of the job.
        slice_height (float): The height of each slice.
        svg_directory (str): The directory to save the SVG files.
        dxf_directory (str): The directory to save the DXF files.

    Returns:
        list: A list of slice_mesh objects representing the 2D slices.
    """
    global progress
    slices = list()
    min_z, max_z = mesh.bounds[:, 2]
    if slice_height == 0:
        slice_height = 0.5
    num_slices = int((max_z - min_z) / slice_height)
    
    if num_slices > 5000:
        num_slices = 5000
        
    for i in range(num_slices):
        z = min_z + i * slice_height

        slice_mesh = mesh.section(
            plane_origin=[0, 0, z], plane_normal=[0, 0, 1])

        # Export the 2D slice as a DXF file
        svg_output_file = os.path.join(svg_directory, f'slice_{i}.svg')
        dxf_output_file = os.path.join(dxf_directory, f'slice_{i}.dxf')
        if not slice_mesh == None and type(slice_mesh) == trimesh.path.path.Path3D:
            slice_mesh.export(dxf_output_file, file_type='dxf')
            slice_mesh.to_planar()[0].export(
                svg_output_file, file_type='svg')
            slices.append(slice_mesh)
        if not progress == round((i/(num_slices*4)*100)):
            update_progress(
                round((i/(num_slices*4)*100)), job_name)
    return slices


def extrude_dxfs(input_folder: str, output_folder: str, job_name: str, slice_height: float) -> bool:
    """
    Extrudes DXF files from the input folder and saves the extruded meshes as STL files in the output folder.

    Args:
        input_folder (str): The path to the folder containing the DXF files.
        output_folder (str): The path to the folder where the extruded meshes will be saved.
        job_name (str): The name of the job.
        slice_height (float): The height of each slice for extrusion.

    Returns:
        bool: True if the function executes successfully.

    """
    
    file_count = len(os.listdir(input_folder))
    for index, filename in enumerate(os.listdir(input_folder)):
        if filename.endswith(".dxf"):
            dxf_path = os.path.join(input_folder, filename)
            mesh = trimesh.load(dxf_path)
            if type(mesh) == trimesh.path.path.Path2D:
                # Extract the 2D polygons from the 3D mesh
                polygons = mesh.polygons_full

                # Define the translation matrix for extrusion
                translation_matrix = np.eye(4)
                translation_matrix[2, 3] = slice_height

                # Extrude each polygon individually
                extruded_meshes = []
                for polygon in polygons:
                    if hasattr(trimesh, "creation"):
                        extruded_mesh = trimesh.creation.extrude_polygon(
                            polygon, slice_height, transform=None)
                        extruded_meshes.append(extruded_mesh)

                # Merge the extruded meshes into a single mesh
                combined_mesh = trimesh.util.concatenate(
                    extruded_meshes)

                # Save the extruded mesh as STL
                stl_filename = filename.replace(
                    ".dxf", "_extruded.stl")
                stl_path = os.path.join(output_folder, stl_filename)
                if type(combined_mesh) == trimesh.base.Trimesh:
                    combined_mesh.export(stl_path, file_type="stl")
            if not progress == round((index/(file_count*4)*100)+25):
                update_progress(
                    round((index/(file_count*4)*100)+25), job_name)
    return True

def combine_stls(output_folder: str, job_name: str, slice_height: float, output_path: str) -> bool:
    """
    Combine multiple STL files into a single mesh and export it as an STL file.

    Args:
        output_folder (str): Path to the folder containing the STL files.
        job_name (str): Name of the job.
        slice_height (float): Height of each slice.
        output_path (str): Path to save the combined mesh as an STL file.

    Returns:
        bool: True if the operation is successful, False otherwise.
    """
    global progress
    meshes = []
    stls = []

    for filename in os.listdir(output_folder):
        if filename.endswith(".stl"):
            stls.append(filename)

    names_of_stls = sorted(stls, key=extract_numeric_prefix)

    # Use the provided extrusion height
    translation_vector = [0, 0, slice_height]
    cumulative_translation = [0, 0, 0]
    stl_name_length = len(names_of_stls)
    print(stl_name_length)
    for index, name in enumerate(names_of_stls):
        stl_path = os.path.join(output_folder, name)
        mesh = trimesh.load(stl_path)

        # Calculate the translation for the current mesh
        mesh_translation = [coord + cum_trans for coord,
                            cum_trans in zip(translation_vector, cumulative_translation)]
        if type(mesh) == trimesh.base.Trimesh:
        # Apply the translation to the current mesh
            moved_mesh = move_mesh(mesh, mesh_translation)

            # Append the translated mesh to the list
            meshes.append(moved_mesh)

            # Update the cumulative translation for the next mesh
            cumulative_translation = mesh_translation
            if not progress == round((index/(stl_name_length*4)*100)+50):
                update_progress(
                    round((index/(stl_name_length*4)*100)+50), job_name)
        else: 
            return False

    combined_vertices = []
    combined_faces = []

    # Loop through each mesh and update the vertices and faces
    vertex_offset = 0
    mesh_count = len(meshes)
    print(mesh_count)
    for index, mesh in enumerate(meshes):
        combined_vertices.extend(mesh.vertices.tolist())
        combined_faces.extend(
            (mesh.faces + vertex_offset).tolist())
        vertex_offset += len(mesh.vertices)
        if not progress == round((index/(mesh_count*4)*100)+75):
            update_progress(
                round((index/(mesh_count*4)*100)+75), job_name)

    # Create the combined mesh
    try:
        combined_mesh = trimesh.Trimesh(vertices=combined_vertices, faces=combined_faces) #pyright: ignore
    except:
        return False
    combined_mesh.export(output_path, file_type="stl")
    update_progress(100, job_name)
    return True

def numerical_sort(item: str) -> int:
    """
    Returns the int for numerical sorting
    
    Args:
        item (str): The string to be sorted.
        
    Returns:
        int: The numerical value obtained after splitting the string and extracting the number.
    """
    number = int(item.split('slice_')[1].split('.')[0])
    return number

def allowed_file(filename: str) -> bool:
    """
    Check if a given filename is allowed.

    Parameters:
    - filename (str): The name of the file to check.

    Returns:
    - bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'stl'}

def generate_unique_folder_name() -> str:
    """
    Generates a unique folder name using the current timestamp and random characters.

    Returns:
        str: The generated folder name.
    """

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_chars = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    folder_name = f'job_{timestamp}_{random_chars}'
    return folder_name

def rotate_mesh(mesh: trimesh.base.Trimesh, rotations: list) -> trimesh.base.Trimesh:
    """
    Rotate a mesh object in 3D space using given rotations around x, y, and z axes.

    Parameters:
    - mesh (trimesh.base.Trimesh): The mesh object to be rotated.
    - rotations (list): A list of three rotation angles in degrees, representing rotations around x, y, and z axes.

    Returns:
    - trimesh.base.Trimesh: The rotated mesh object.
    """
    radians = np.radians(rotations)

    # Create rotation matrices around x, y and z axes
    Rx = np.array([[1, 0, 0],
                [0, np.cos(radians[0]), -np.sin(radians[0])],
                [0, np.sin(radians[0]), np.cos(radians[0])]])

    Ry = np.array([[np.cos(radians[1]), 0, np.sin(radians[1])],
                [0, 1, 0],
                [-np.sin(radians[1]), 0, np.cos(radians[1])]])

    Rz = np.array([[np.cos(radians[2]), -np.sin(radians[2]), 0],
                [np.sin(radians[2]), np.cos(radians[2]), 0],
                [0, 0, 1]])

    # Combine the rotations in the order: Rz * Ry * Rx
    R = np.dot(Rz, np.dot(Ry, Rx))
    rotated_vertices = np.dot(mesh.vertices, R.T)
    rotated_mesh = trimesh.Trimesh(vertices=rotated_vertices, faces=mesh.faces)
    return rotated_mesh


def scale_mesh(mesh: trimesh.base.Trimesh, scale: float) -> trimesh.base.Trimesh:
    """
    Scale a mesh object in 3D space using the given scale factor.

    Parameters:
    - mesh (trimesh.base.Trimesh): The mesh object to be scaled.
    - scale (float): The scale factor to be applied to the mesh object.

    Returns:
    - trimesh.base.Trimesh: The scaled mesh object.
    """
    if isinstance(scale, (int, float)):
        # Uniform scaling if a single value is provided
        scaled_mesh = mesh.copy()
        scaled_mesh.apply_scale(scale)
    elif isinstance(scale, tuple) and len(scale) == 3:
        # Non-uniform scaling if a tuple with three values is provided
        scaled_mesh = mesh.copy()
        scaled_mesh.apply_scale([scale[0], scale[1], scale[2]])
    else:
        raise ValueError(
            'Invalid scale parameter. It should be a float or a tuple of three floats.')

    return scaled_mesh