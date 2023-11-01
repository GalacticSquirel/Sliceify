import re
import json
import os
import trimesh
import numpy as np
from flask import Flask, redirect, render_template, request, flash, redirect, send_file, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import shutil
import random
import string
import datetime
app = Flask(__name__)

app.config['SECRET_KEY'] = "sdsaed1231dah£%!'^£*&'£"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'stl'}




def rotate_mesh(mesh, rotations):
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
    # rotated_mesh.show()
    return rotated_mesh


def scale_mesh(mesh, scale):
    '''
    Scales a trimesh mesh by a given factor.

    Parameters:
        mesh (trimesh.Trimesh): The input mesh object.
        scale (float or tuple): Scaling factor. If a float, it scales uniformly in all dimensions.
                                If a tuple (sx, sy, sz), it scales independently along each axis.

    Returns:
        trimesh.Trimesh: The scaled mesh.
    '''
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


def generate_unique_folder_name():
    """
    Generates a unique folder name using the current timestamp and random characters.

    Returns:
        str: The generated folder name.
    """

    # Generate a unique folder name using timestamp and random characters
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    random_chars = ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=6))
    folder_name = f'job_{timestamp}_{random_chars}'
    return folder_name


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Route for the index page. Handles both GET and POST requests.

    Parameters:
    None

    Returns:
    The rendered index.html template if the request method is GET.
    Redirects to the index page if the request method is POST and the file part is missing.
    Redirects to the index page if the request method is POST and no file is selected.
    Redirects to the index page if the request method is POST and the selected file is not allowed.
    Redirects to the initial configuration page if the request method is POST and the file is valid.
    """
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect('/')
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty part without a filename
        if file.filename == '':
            flash('No selected file')
            return redirect('/')
        if file and allowed_file(file.filename):

            folder_name = generate_unique_folder_name()
            try:
                os.makedirs(os.path.join('static', folder_name))
                os.makedirs(os.path.join('static', folder_name, 'upload'))
                print(f'Created folder: {folder_name} in static')
                filename = secure_filename(file.filename)
                filepath = os.path.join(
                    'static', folder_name, 'upload/upload.stl')
                print(filepath)
                file.save(filepath)
                # return slice_stl_file(filepath,folder_name,3)
                return initial_configuration(folder_name, 3)
            except OSError as e:
                print(f'Error creating folder: {e}')
                flash('Error creating folder')
    return render_template('index.html')


@app.route('/viewstl/<string:job_name>', methods=['GET'])
def viewstl(job_name):
    """
    This function is a route handler for the '/viewstl/<string:job_name>' endpoint.
    It takes in a string parameter 'job_name' which is used to construct a file path.
    The function prints the file path and then returns a rendered template 'slices.html'
    with the 'path' variable set to the constructed file path.

    Parameters:
    job_name (str): The name of the job used to construct the file path.

    Returns:
    A rendered template 'slices.html' with the 'path' variable set to the combined stl file path.
    """
    print(os.path.join('static', job_name, 'combined_output.stl'))
    path = f'/static/{job_name}/combined_output.stl'
    return render_template('slices.html', path=path)


@app.route('/viewfiles/<string:job_name>/<string:path>')
@app.route('/viewfiles/<string:job_name>')
def viewfiles(job_name, path=None):
    """
    Route decorator for viewing files in a given job.

    Parameters:
        job_name (str): The name of the job.
        path (str, optional): The path to the files. Defaults to None.

    Returns:
        str: The rendered template for viewing files.
    """

    print(job_name)
    if path:
        print(path)
        items = os.listdir(os.path.join(
            app.root_path, 'static', job_name, path))
        return render_template('viewfiles.html', items=items, job_name=job_name, download_path=f'{job_name}/{path}')
    else:
        items = os.listdir(os.path.join(app.root_path, 'static', job_name))
        return render_template('viewfiles.html', items=items, job_name=job_name, download_path=job_name)


@app.route('/downloaddxfs/<string:job_name>')
def download_dxf(job_name):
    """
    Downloads a ZIP file containing DXF files from the specified folder.

    Args:
        job_name (str): The name of the job.

    Returns:
        str: The ZIP file containing the DXF files.

    Raises:
        Exception: If an error occurs during the download process.
    """
    import zipfile
    try:
        # Create a ZIP file containing the contents of the specified folder
        zip_filename = f'static/{job_name}/{job_name}_dxf_layers.zip'
        folder_path = f'static/{job_name}/dxf_layers'
        folder_abs_path = os.path.join(app.root_path, folder_path)
        print(zip_filename, folder_path, folder_abs_path)
        # Create the ZIP file in memory
        zip_buffer = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)

        # Add DXF files to the ZIP file with the desired folder structure
        for filename in os.listdir(folder_abs_path):
            if filename.endswith('.dxf'):
                src_file = os.path.join(folder_abs_path, filename)
                zip_file_path = os.path.join('output_dxf_layers', filename)
                zip_buffer.write(src_file, zip_file_path)
        zip_buffer.close()

        return send_file(zip_filename, as_attachment=True)

    except Exception as e:
        print('e')
        return str(e)


def numerical_sort(item):
    number = int(item.split('slice_')[1].split('.')[0])
    return number


@app.route('/viewdxf//<string:job_name>/<string:folder>/<string:file>')
def viewdxf(job_name, folder, file):
    """
    View a DXF file.

    Parameters:
        job_name (string): The name of the job.
        folder (string): The folder containing the DXF file.
        file (string): The name of the DXF file.

    Returns:
        The rendered DXF template with the list of SVG files and the initial index.
    """

    svgs = list(map(lambda x: url_for('static', filename=f'{job_name}/{folder.replace('dxf_', 'svg_')}/{x.replace(
        '.dxf', '.svg')}'), sorted(os.listdir(os.path.join('static', job_name, folder)), key=numerical_sort)))
    print(svgs)
    return render_template('dxf.html', svgs=svgs, initial_index=int(file.split('.')[0].split('_')[1])-1)
    # return url_for('static',filename=f'{job_name}/{folder}/{file}')





@app.route('/submitconfig/<job_name>/<int:slice_height>/<string:rotations>', methods=['POST'])
def submit_config(job_name, slice_height, rotations):
    """
    Submits a configuration for a job and processes the input file to generate 2D slices.

    Args:
        job_name (str): The name of the job.
        slice_height (int): The height of each slice in millimeters.

    Returns:
        Response: A JSON response indicating the success of the operation.
    """
    try:
        success = False
        json.dump({'progress': 0}, open(os.path.join(
            'static', job_name, 'data.json'), "w"))
        progress = 0

        def extract_numeric_prefix(filename):
            match = re.match(r'slice_(\d+)_extruded\.stl', filename)
            return int(match.group(1)) if match else 0

        def move_mesh(mesh, translation_vector):
            new_mesh = mesh.copy()  # Create a copy to avoid modifying the original mesh
            new_mesh.apply_translation(translation_vector)
            return new_mesh

        def remove_duplicate_vertices(mesh):
            # Remove duplicate vertices from the mesh
            mesh.vertices, unique_indices = trimesh.grouping.unique_rows(
                mesh.vertices)
            mesh.faces = unique_indices[mesh.faces]
            return mesh

        def compute_vertex_normals(mesh):
            # Compute vertex normals for the mesh
            mesh.compute_normals()
            return mesh

        input_file = os.path.join('static', job_name, 'upload/upload.stl')

        mesh = trimesh.load(input_file)
        # mesh = scale_mesh(mesh, 30)

        
        
        rotations = list(map(lambda x: int(x), rotations.split(",")))

        mesh = rotate_mesh(mesh, rotations)
        min_z, max_z = mesh.bounds[:, 2]
        # Calculate the number of slices needed
        num_slices = int((max_z - min_z) / slice_height)
        print(num_slices)
        dxf_directory = os.path.join('static', job_name, 'dxf_layers')
        svg_directory = os.path.join('static', job_name, 'svg_layers')
        if not os.path.exists(dxf_directory):
            print(f"Making: {dxf_directory}")
            os.makedirs(dxf_directory)
        else:
            import shutil
            shutil.rmtree(dxf_directory)
            os.makedirs(dxf_directory)
        if not os.path.exists(svg_directory):
            os.makedirs(svg_directory)
        else:
            import shutil
            shutil.rmtree(svg_directory)
            os.makedirs(svg_directory)

        to_show = []
        # Slice the mesh and export 2D files

        for i in range(num_slices):
            z = min_z + i * slice_height
            
            slice_mesh = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])

            # Export the 2D slice as a DXF file
            svg_output_file = os.path.join(svg_directory, f'slice_{i}.svg')
            dxf_output_file = os.path.join(dxf_directory, f'slice_{i}.dxf')

            if not slice_mesh == None:
                slice_mesh.export(dxf_output_file, file_type='dxf')
                # print(slice_mesh.to_planar()[0])
                slice_mesh.to_planar()[0].export(svg_output_file, file_type='svg')

                to_show.append(slice_mesh)
            if not progress == round((i/(num_slices*4)*100)):
                progress = update_progress(round((i/(num_slices*4)*100)), job_name)
            # print(round((i/(num_slices*4)*100)),1)
        if not to_show == None:
            success = True

            job_path = os.path.join('static', job_name)
            input_folder = os.path.join(job_path, 'dxf_layers')
            output_folder = os.path.join(job_path, 'output_stl_layers')
            output_path = f'{job_path}//combined_output.stl'

            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            else:
                import shutil
                shutil.rmtree(output_folder)
                os.makedirs(output_folder)
            file_count = len(os.listdir(input_folder))
            print(file_count)
            for index, filename in enumerate(os.listdir(input_folder)):
                if filename.endswith(".dxf"):
                    dxf_path = os.path.join(input_folder, filename)
                    mesh = trimesh.load(dxf_path)

                    # Extract the 2D polygons from the 3D mesh
                    polygons = mesh.polygons_full

                    # Define the translation matrix for extrusion
                    translation_matrix = np.eye(4)
                    translation_matrix[2, 3] = slice_height

                    # Extrude each polygon individually
                    extruded_meshes = []
                    for polygon in polygons:
                        extruded_mesh = trimesh.creation.extrude_polygon(
                            polygon, slice_height, transform=None)
                        extruded_meshes.append(extruded_mesh)

                    # Merge the extruded meshes into a single mesh
                    combined_mesh = trimesh.util.concatenate(extruded_meshes)

                    # Save the extruded mesh as STL
                    stl_filename = filename.replace(".dxf", "_extruded.stl")
                    stl_path = os.path.join(output_folder, stl_filename)
                    combined_mesh.export(stl_path, file_type="stl")
                if not progress == round((index/(file_count*4)*100)+25):
                    progress = update_progress(
                        round((index/(file_count*4)*100)+25), job_name)
                    # print(round((index/(file_count*4)*100))+25,2)

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

                # Apply the translation to the current mesh
                moved_mesh = move_mesh(mesh, mesh_translation)

                # Append the translated mesh to the list
                meshes.append(moved_mesh)

                # Update the cumulative translation for the next mesh
                cumulative_translation = mesh_translation
                if not progress == round((index/(stl_name_length*4)*100)+50):
                    progress = update_progress(
                        round((index/(stl_name_length*4)*100)+50), job_name)
                # print(round((index/(stl_name_length*4)*100))+50,3)
            combined_vertices = []
            combined_faces = []

            # Loop through each mesh and update the vertices and faces
            vertex_offset = 0
            mesh_count = len(meshes)
            print(mesh_count)
            for index, mesh in enumerate(meshes):
                combined_vertices.extend(mesh.vertices.tolist())
                combined_faces.extend((mesh.faces + vertex_offset).tolist())
                vertex_offset += len(mesh.vertices)
                if not progress == round((index/(mesh_count*4)*100)+75):
                    progress = update_progress(
                        round((index/(mesh_count*4)*100)+75), job_name)

                # print(round((index/(mesh_count*4)*100))+75,4)
            # Create the combined mesh
            combined_mesh = trimesh.Trimesh(
                vertices=combined_vertices, faces=combined_faces)

            combined_mesh.export(output_path, file_type="stl")
            update_progress(100, job_name)
            success = True
    except Exception as e:
        raise(e)
        success = False
    resp = jsonify(success)
    resp.status_code = 200
    return resp


def update_progress(curr_progress, job_name):
    json.dump({'progress': curr_progress}, open(
        os.path.join('static', job_name, 'data.json'), "w"))
    return curr_progress


def initial_configuration(job_name, slice_height):
    path = f'/static/{job_name}/upload/upload.stl'
    return render_template('config.html', path=path, job_name=job_name, slice_height=slice_height)
# add maximum slice size by doing half of width


@app.route('/progress/<job_name>', methods=["GET", "POST"])
def progress(job_name):
    if request.method == "GET":
        return render_template('progress.html', job_name=job_name)
    else:
        progress = json.load(open(os.path.join('static', job_name, 'data.json'), "r"))[
            "progress"]
        return str(progress)


@app.route('/<job_name>')
def output(job_name):
    return render_template("success.html", job_name=job_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
