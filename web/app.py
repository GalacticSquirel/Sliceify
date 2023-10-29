import os
import trimesh
import numpy as np
from flask import Flask, redirect, render_template, request,flash, redirect,send_file,url_for
from werkzeug.utils import secure_filename
import batch_extrude as batch
import os
import shutil
import random
import string
import datetime
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'stl'}
def rotate_mesh(mesh, axis, degrees):
    """
    Rotate a trimesh object around the specified axis by the given angle in degrees.

    Parameters:
        mesh (trimesh.Trimesh): The input trimesh object.
        axis (str): The axis around which to rotate the mesh. Can be 'x', 'y', or 'z'.
        degrees (float): The rotation angle in degrees.

    Returns:
        trimesh.Trimesh: A new trimesh object with the rotated vertices.
    """
    if axis not in ['x', 'y', 'z']:
        raise ValueError("Invalid axis. Supported axes are 'x', 'y', or 'z'.")

    angle_radians = np.radians(degrees)

    # Define the rotation matrix based on the specified axis
    if axis == 'x':
        rotation_matrix = np.array([[1, 0, 0],
                                    [0, np.cos(angle_radians), -np.sin(angle_radians)],
                                    [0, np.sin(angle_radians), np.cos(angle_radians)]])
    elif axis == 'y':
        rotation_matrix = np.array([[np.cos(angle_radians), 0, np.sin(angle_radians)],
                                    [0, 1, 0],
                                    [-np.sin(angle_radians), 0, np.cos(angle_radians)]])
    else:  # axis == 'z'
        rotation_matrix = np.array([[np.cos(angle_radians), -np.sin(angle_radians), 0],
                                    [np.sin(angle_radians), np.cos(angle_radians), 0],
                                    [0, 0, 1]])

    # Apply the rotation to the mesh vertices
    rotated_vertices = np.dot(mesh.vertices, rotation_matrix)

    # Create a new trimesh object with the rotated vertices
    rotated_mesh = trimesh.Trimesh(vertices=rotated_vertices, faces=mesh.faces)
    # rotated_mesh.show()
    return rotated_mesh
def scale_mesh(mesh, scale):
    """
    Scales a trimesh mesh by a given factor.

    Parameters:
        mesh (trimesh.Trimesh): The input mesh object.
        scale (float or tuple): Scaling factor. If a float, it scales uniformly in all dimensions.
                                If a tuple (sx, sy, sz), it scales independently along each axis.

    Returns:
        trimesh.Trimesh: The scaled mesh.
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
        raise ValueError("Invalid scale parameter. It should be a float or a tuple of three floats.")

    return scaled_mesh
def generate_unique_folder_name():
    
    # Generate a unique folder name using timestamp and random characters
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    folder_name = f"job_{timestamp}_{random_chars}"
    return folder_name

@app.route('/', methods=['GET', 'POST'])
def index():
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
                print(f"Created folder: {folder_name} in static")
                filename = secure_filename(file.filename)
                filepath = os.path.join('static',folder_name, 'upload', filename)
                file.save(filepath)
                return slice_stl_file(filepath,folder_name,3)
            except OSError as e:
                print(f"Error creating folder: {e}")
                flash('Error creating folder')
    return render_template('index.html')
@app.route('/viewstl/<string:job_name>', methods=['GET'])
def viewstl(job_name):
    print(os.path.join("static",job_name,"combined_output.stl"))
    path = f"/static/{job_name}/combined_output.stl"
    return render_template('slices.html', path=path)

@app.route('/viewfiles/<string:job_name>/<string:path>')
@app.route('/viewfiles/<string:job_name>')
def viewfiles(job_name,path=None):
    
    print(job_name)
    if path:
        print(path)
        items = os.listdir(os.path.join(app.root_path, 'static',job_name,path))
        return render_template('viewfiles.html', items=items,job_name=job_name, download_path=f"{job_name}/{path}")
    else:
        items = os.listdir(os.path.join(app.root_path, 'static',job_name))
        return render_template('viewfiles.html', items=items,job_name=job_name, download_path=job_name)
    
@app.route('/downloaddxfs/<string:job_name>')
def download_dxf(job_name):
    import zipfile
    try:
        # Create a ZIP file containing the contents of the specified folder
        zip_filename = f"{job_name}_dxf_layers.zip"
        folder_path = f"static/{job_name}/dxf_layers"
        folder_abs_path = os.path.join(app.root_path, folder_path)
        
        # Create the ZIP file in memory
        zip_buffer = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        
        # Add DXF files to the ZIP file with the desired folder structure
        for filename in os.listdir(folder_abs_path):
            if filename.endswith('.dxf'):
                src_file = os.path.join(folder_abs_path, filename)
                zip_file_path = os.path.join('output_dxf_layers', filename)
                zip_buffer.write(src_file, zip_file_path)
        
        # Close the ZIP buffer
        zip_buffer.close()
        # Redirect to the index route after initiating the download
        return send_file(zip_filename, as_attachment=True)  # Replace 'index' with your actual index route function name
    except Exception as e:
        return str(e)
def numerical_sort(item):
    number = int(item.split("slice_")[1].split(".")[0])
    return number
@app.route('/viewdxf//<string:job_name>/<string:folder>/<string:file>')
def viewdxf(job_name, folder, file):

    svgs=list(map(lambda x: url_for('static',filename=f"{job_name}/{folder.replace('dxf_','svg_')}/{x.replace('.dxf','.svg')}"),sorted(os.listdir(os.path.join('static',job_name,folder)), key=numerical_sort)))
    print(svgs)
    return render_template('dxf.html', svgs=svgs,initial_index=int(file.split(".")[0].split("_")[1])-1)
    # return url_for('static',filename=f"{job_name}/{folder}/{file}")

@app.route('/rotate/<job_name>/<axis>/<degrees>')
def rotate_upload(job_name, axis, degrees):
    path_of_stl = os.path.join('static', job_name, 'upload', os.listdir(os.path.join('static', job_name, 'upload'))[0])
    mesh = trimesh.load(path_of_stl)
    rotate_mesh(mesh, axis,int(degrees)).export(path_of_stl)
    
    return [ axis, degrees]

def initial_rotation(filepath, foldername):
    pass
# slice_stl_file(filepath,folder_name,3) should be returned after a final submit button is pressed. it should be same 
# gui as for viewing combined stl except camera should not be moveable but zoom should still be there. The viewer should get roladed
# after each button press except submit, so need to change rotate_upload() so it returns the viewer as a call should be made to rotate
# _viewer() on each rotation
def slice_stl_file(input_file, output_directory, slice_height=3):
    
    # Load and process the STL file
    mesh = trimesh.load(input_file)
    # mesh = rotate_mesh(mesh, "x", 90)
    # mesh = rotate_mesh(mesh, "y", 270)
    # mesh = rotate_mesh(mesh, "z", 90)
    mesh = scale_mesh(mesh, 30)

    min_z, max_z = mesh.bounds[:, 2]

    # Calculate the number of slices needed
    num_slices = int((max_z - min_z) / slice_height)
    print(num_slices)
    dxf_directory = os.path.join('static', output_directory,"dxf_layers")
    svg_directory = os.path.join('static', output_directory,"svg_layers")
    os.makedirs(dxf_directory, exist_ok=True)
    os.makedirs(svg_directory, exist_ok=True)
    to_show = []
    # Slice the mesh and export 2D files
    for i in range(num_slices):
        z = min_z + i * slice_height
        slice_mesh = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])

        # Export the 2D slice as a DXF file
        svg_output_file = os.path.join(svg_directory,f"slice_{i}.svg")
        dxf_output_file = os.path.join(dxf_directory,f"slice_{i}.dxf")
        
        if not slice_mesh==None:
            slice_mesh.export(dxf_output_file, file_type="dxf", version="2000")
            print(slice_mesh.to_planar()[0])
            slice_mesh.to_planar()[0].export(svg_output_file, file_type="svg")
            

            to_show.append(slice_mesh)
    if not to_show==None:
        success = False
        try:
            job_path = os.path.join("static", output_directory)
            input_folder = os.path.join(job_path,"dxf_layers")
            output_folder = os.path.join(job_path,"output_stl_layers")
            output_path = f"{job_path}//combined_output.stl"
            batch.extrude_trimesh_dxf_to_stl(input_folder, output_folder,3)
            batch.combine_stl_files(output_folder, output_path,3)
            success = True
        except Exception as e:
            print(e)
        if success:
            return render_template('success.html', job_name=output_directory)
    else:
        print("nothing in to_show")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
