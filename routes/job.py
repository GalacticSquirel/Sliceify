global progress
from sqlalchemy.engine import url
from imports import *
from logic.logic import *
from routes.user import db
def init_job(app: flask.app.Flask) -> flask.app.Flask:
    
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

    @app.route('/downloadfolder/<job_name>/<path:path>')
    def downloadfolder(job_name: str, path: str) -> werkzeug.wrappers.response.Response:
        """
        This function handles the '/download_folder/<job_name>/<path>' route. 
        It creates a ZIP file of the folder specified by 'path' within the job specified by 'job_name'.

        Parameters:
        job_name (str): The name of the job containing the folder to be zipped.
        path (str): The path of the folder to be zipped, relative to the job folder.

        Returns:
        A Flask response that triggers the download of the ZIP file.

        Error Responses:
        - Returns "Error: Cannot zip the 'zip' folder." with a 400 status code if the requested folder is 'zip' (case-insensitive).
        - Returns "Error: The requested folder does not exist." with a 404 status code if the requested folder does not exist.
        
        """
        if path.lower() == 'zip':
            return Response("Error: Cannot zip the 'zip' folder.", status=400)
        if not os.path.exists(f"{app.root_path}/static/{job_name}/{path}"):
            return Response("Error: The requested folder does not exist.", status=404)
        
        zip_folder_path = os.path.join(app.root_path, 'static', job_name, 'zip')
        os.makedirs(zip_folder_path, exist_ok=True)
        zip_filename = os.path.join(zip_folder_path, f'{path}.zip')
        folder_path = os.path.join(app.root_path, 'static', job_name, path)
        zip_buffer = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                src_file = os.path.join(root, file)
                zip_file_path = os.path.relpath(src_file, folder_path)
                zip_buffer.write(src_file, zip_file_path)
        zip_buffer.close()

        return send_file(zip_filename, as_attachment=True)

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
            print(url_for('output', job_name=job_name))
            return render_template('job/progress.html', job_name=job_name, job_route=url_for('output', job_name=job_name))
        else:
            progress = json.load(open(os.path.join('static', job_name, 'data.json'), "r"))[
                "progress"]
            return str(progress)


    @app.route('/job/<string:job_name>')
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
    
    from flask import request, jsonify

    @app.route('/deletejob/<string:job_name>', methods=['GET'])
    @job_belongs_to_user
    def deletejob(job_name: str) -> werkzeug.wrappers.response.Response:
        """
        This function handles the '/delete_job' route. 
        It deletes the job specified in the request data if it belongs to the currently logged-in user.
        
        Args:
            job_name (str): The name of the job.

        Returns:
            str: A JSON response indicating the result of the operation.
        """
        curr_jobs = json.loads(current_user.jobs)
        if job_name in curr_jobs:
            shutil.rmtree(os.path.join(app.root_path, 'static', job_name))
            curr_jobs.remove(job_name)
            current_user.jobs = json.dumps(curr_jobs)
            db.session.commit()
            return redirect(url_for('account'))
        
        return redirect(url_for('account'))
    
    return app