from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_talisman import Talisman
from werkzeug.security import generate_password_hash
from sqlalchemy import CheckConstraint
import json
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = "sdsaed1231dah£%!'^£*&'£"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
csp = {
    'default-src': [
        '\'self\'',
        'https://unpkg.com',
        
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://unpkg.com',
        'blob:',
        'https://code.jquery.com',
        'https://cdn.rawgit.com',
        'https://cdn.jsdelivr.net',
        'https://stackpath.bootstrapcdn.com',
        'https://cdnjs.cloudflare.com',
        
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'https://cdnjs.cloudflare.com',
        'https://fonts.googleapis.com',
    ],
    'img-src': [ 
        '\'self\'',
        'data:', 
        'https://flowbite.com',
        'https://flowbite.s3.amazonaws.com'
    ],
    'font-src': [
        '\'self\'',
        'https://fonts.googleapis.com',
        'https://fonts.gstatic.com'
    ],
}
Talisman(app, content_security_policy=csp)
db = SQLAlchemy(app)
CORS(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model): 
    id = db.Column(db.Integer, primary_key=True,autoincrement=True) 
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    verified = db.Column(db.Integer, CheckConstraint('verified IN (0, 1)'))
    verify_token = db.Column(db.String(1000))
    jobs = db.Column(db.String())
    otp_token = db.Column(db.String(1000))
    def __init__(self, email: str, password: str, name: str, verified: int, verify_token: str, jobs: list) -> None:
        self.email = email
        self.password = generate_password_hash(str(password), method='pbkdf2:sha256')
        self.name = name
        self.verified = verified
        self.verify_token = verify_token
        self.jobs = json.dumps(jobs)
        self.otp_token = None


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))