from imports import *
from logic.logic import *
from routes.user import init_user
from routes.job import init_job


app = init_user(app)
app = init_job(app)


@app.route('/')
def index() -> str:
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port, debug=True)
