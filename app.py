from imports import *
from logic.logic import *
from routes.user import init_user
from routes.job import init_job

app = Flask(__name__)


init_user(app)
init_job(app)


@app.route('/', methods=['GET', 'POST'])
def index() -> Union[str, werkzeug.wrappers.response.Response]:

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
                print(filepath)
                file.save(filepath)
                # return slice_stl_file(filepath,folder_name,3)
                return initial_configuration(folder_name, 3)
            except OSError as e:
                print(f'Error creating folder: {e}')
                flash('Error creating folder')
    return render_template('index.html')




if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port, debug=True)
