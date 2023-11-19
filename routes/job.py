global progress
from imports import *
from logic.logic import *
from routes.user import db
def init_job(app):
    
    @app.route('/start', methods=['GET', 'POST'])
    @lr
    def start() -> Union[str, werkzeug.wrappers.response.Response]:

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
            if file and file.filename and allowed_file(file.filename):

                folder_name = generate_unique_folder_name()
                try:
                    os.makedirs(os.path.join('static', folder_name))
                    os.makedirs(os.path.join('static', folder_name, 'upload'))
                    print(f'Created folder: {folder_name} in static')
                    filepath = os.path.join(
                        'static', folder_name, 'upload/upload.stl')
                    
                    file.save(filepath)

                    current_user.jobs = json.dumps(json.loads(current_user.jobs) + [folder_name])
                    db.session.commit()
                    
                    return initial_configuration(folder_name, 3)
                except OSError as e:
                    print(f'Error creating folder: {e}')
                    flash('Error creating folder')
        return render_template('job/start.html')

    @app.route('/viewstl/<string:job_name>', methods=['GET'])
    @job_belongs_to_user
    def viewstl(job_name: str) -> str:
        """
        This function is a route handler for the '/viewstl/<string:job_name>' endpoint.
        It takes in a string parameter 'job_name' which is used to construct a file path.
        The function prints the file path and then returns a rendered template 'job/slices.html'
        with the 'path' variable set to the constructed file path.

        Parameters:
        job_name (str): The name of the job used to construct the file path.

        Returns:
        A rendered template 'job/slices.html' with the 'path' variable set to the combined stl file path.
        """
        path = f'/static/{job_name}/combined_output.stl'
        return render_template('job/slices.html', path=path)


    @app.route('/viewfiles/<string:job_name>/<string:path>')
    @app.route('/viewfiles/<string:job_name>')
    @job_belongs_to_user
    def viewfiles(job_name: str, path: Optional[str] = None) -> str:
        """
        Retrieves the list of files in a given job's directory.
        
        Parameters:
            job_name (str): The name of the job.
            path (Optional[str]): The path within the job's directory (default: None).
            
        Returns:
            str: The rendered viewfiles template.
        """

        print(job_name)
        if path:
            print(path)
            items = os.listdir(os.path.join(
                app.root_path, 'static', job_name, path))
            return render_template('job/viewfiles.html', items=items, job_name=job_name, download_path=f'{job_name}/{path}')
        else:
            items = os.listdir(os.path.join(app.root_path, 'static', job_name))
            return render_template('job/viewfiles.html', items=items, job_name=job_name, download_path=job_name)


    @app.route('/downloaddxfs/<string:job_name>')
    @job_belongs_to_user
    def download_dxf(job_name: str) -> Response:
        """
        Downloads the DXF files from the specified job.

        Parameters:
        job_name (str): The name of the job.

        Returns:
        A Response object containing the downloaded DXF files.
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
            raise e
        


    @app.route('/viewdxf//<string:job_name>/<string:folder>/<string:file>')
    @job_belongs_to_user
    def viewdxf(job_name: str, folder: str, file: str) -> str:
        """
        A decorator that creates a route for viewing a DXF file.

        Parameters:
        - job_name (str): The name of the job.
        - folder (str): The folder containing the DXF file.
        - file (str): The name of the DXF file.

        Returns:
        - str: The rendered template for the DXF file.

        Notes:
        - This function assumes that the DXF file is located in the static folder.
        - The DXF file is converted to SVG format before rendering the template.
        """

        svgs = list(map(lambda x: url_for('static', filename=f'{job_name}/{folder.replace('dxf_', 'svg_')}/{x.replace(
            '.dxf', '.svg')}'), sorted(os.listdir(os.path.join('static', job_name, folder)), key=numerical_sort)))
        return render_template('job/dxf.html', svgs=svgs, initial_index=int(file.split('.')[0].split('_')[1])-1)



    @app.route('/submitconfig/<string:job_name>/<float:slice_height>/<string:rotations_str>', methods=['POST'])
    @job_belongs_to_user
    def submit_config(job_name: str, slice_height: float, rotations_str: str) -> Response:
        """
        Submit a configuration for a job.

        Args:
            job_name (str): The name of the job.
            slice_height (float): The height of each slice.
            rotations_str (str): A string representation of a list of rotations.

        Returns:
            Response: The response object containing the success status.

        Raises:
            Exception: If an error occurs during the execution of the function.
        """
        success = False
        print(type(rotations_str))
        try:
            
            json.dump({'progress': 0}, open(os.path.join(
                'static', job_name, 'data.json'), "w"))


            # set directories
            
            input_file = os.path.join('static', job_name, 'upload/upload.stl')
            job_path = os.path.join('static', job_name)
            input_folder = os.path.join(job_path, 'dxf_layers')
            output_folder = os.path.join(job_path, 'output_stl_layers')
            output_path = f'{job_path}//combined_output.stl'
            dxf_directory = os.path.join('static', job_name, 'dxf_layers')
            svg_directory = os.path.join('static', job_name, 'svg_layers')
            
            # load mesh
            mesh = trimesh.load(input_file)
            
            # rotate mesh
            rotations = list(map(lambda x: int(x), rotations_str.split(",")))
            if type(mesh) == trimesh.base.Trimesh:
                mesh = rotate_mesh(mesh, rotations)
            
                remake_if_exist(dxf_directory)
                remake_if_exist(svg_directory)
                remake_if_exist(output_folder)
                
                # Slice the mesh and export 2D files
                
                slices = slice_stl_file(mesh, job_name, slice_height, svg_directory, dxf_directory)


                if not slices == None:
                    success = True
                    if extrude_dxfs(input_folder, output_folder, job_name, slice_height):
                        if combine_stls(output_folder, job_name, slice_height, output_path):
                        
                            success = True
        except Exception as e:
            raise (e)

        resp = jsonify(success)
        resp.status_code = 200
        return resp




    @app.route('/progress/<string:job_name>', methods=["GET", "POST"])
    @job_belongs_to_user
    def progress(job_name: str) -> str:
        """
        Retrieves the progress of a job.

        Args:
            job_name (str): The name of the job.

        Returns:
            str: The progress of the job as a string.
        """
        if request.method == "GET":
            return render_template('job/progress.html', job_name=job_name)
        else:
            progress = json.load(open(os.path.join('static', job_name, 'data.json'), "r"))[
                "progress"]
            return str(progress)


    @app.route('/<string:job_name>')
    @job_belongs_to_user
    def output(job_name: str) -> str:
        """
        Render the job/success.html template with the given job name.

        Args:
            job_name (str): The name of the job.

        Returns:
            str: The rendered template.
        """
        return render_template("job/success.html", job_name=job_name)
    
    return app