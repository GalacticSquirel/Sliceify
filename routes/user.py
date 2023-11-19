from imports import *
from logic.logic import *


def init_user(app: flask.app.Flask) -> flask.app.Flask:
    """
    Initialize the user module by configuring the Flask app, setting up the database,
    and defining routes for user-related functionality such as signup, login, and account management.

    Args:
        app (flask.app.Flask): The Flask app instance.

    Returns:
        flask.app.Flask: The initialized Flask app instance.
    """


    @app.route('/signup', methods=['POST','GET']) 
    def signup() -> Union[werkzeug.wrappers.response.Response,str]:
        """
        This function handles the sign up process. It accepts both GET and POST requests to the '/signup' route.
        If the request method is POST, the function retrieves the user object and performs the sign up process.
        It checks if the user is already signed in, and if not, it retrieves the email, username, and password from the request form.
        It validates the email, username, and password, and if any of them are invalid, it redirects the user to the signup page
        with an appropriate flash message.
        If the email is already registered in the database, the user is redirected to the signup page with a flash message indicating
        that the email address already exists.
        If the input values are valid, a new user object is created and added to the database. An email verification token is
        generated and associated with the user. An email verification link is sent to the user's email address using the email_handler module.
        Finally, the user is logged in and redirected to the account page.

        If the request method is GET, the function renders the signup.html template.

        Returns:
            Union[werkzeug.wrappers.response.Response,str]: The response object or a string indicating failure
        """
        
        if request.method == 'POST':
            user = current_user._get_current_object()
            if not type(user) is User:
                email = str(request.form.get('email'))
                username = str(request.form.get('username'))
                password = str(request.form.get('password'))
                print(email, username, password)

                regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                if not (re.fullmatch(regex, email)):
                    flash("Invalid Email")
                    return redirect(url_for('signup'))

                if username == "":
                    flash("Invalid Name, you must have one")
                    return redirect(url_for('signup'))
                if len(list(str(username))) < 4:
                    flash("Invalid Name, must be at least 4 characters")
                    return redirect(url_for('signup'))

                if not password_check(str(password)):
                    flash("Invalid Password, include at least one upper and lower letters and one number and a special character")
                    return redirect(url_for('signup'))

                # if this returns a user, then the email already exists in database
                user = User.query.filter_by(email=email).first()
                if user:  
                    flash('Email address already exists')
                    return redirect(url_for('signup'))

                token = str(uuid.uuid4())
                
                new_user = User(email=email, password=password, name=str(username),  verified=0, verify_token=token, jobs=list())
                print(email,username, password, 0, token, 0, list())
                
                send_verify_email(url_for('verify', token=token, _external=True), email)
                
                db.session.add(new_user)
                db.session.commit()            
                user = User.query.filter_by(email=email).first()
                login_user(user)
                return redirect(url_for('account'))
            else:
                flash("Failed to sign up")
                return redirect(url_for('signup'))
        else:
            return render_template('forms/signup.html')


    @app.route('/login', methods=['GET', 'POST']) 
    def login() -> Union[werkzeug.wrappers.response.Response,str]:
        """
        Define login page path.

        This function handles the '/login' route and supports both GET and POST methods. If the request is a GET, it returns the login page. 
        If the request is a POST, it checks if the user exists in the database and if the password matches.
        If the user is found and the password is correct, the user is logged in and redirected to the account page. 
        Otherwise, appropriate error messages are flashed and the user is redirected to the appropriate pages ('signup' or 'login').

        Returns:
            Union[werkzeug.wrappers.response.Response, str]: The login page or a redirect.
        """
        if current_user.is_authenticated:
            return redirect(url_for('account'))
        user = current_user._get_current_object()
        if not type(user) is User:
            if request.method == 'GET':  # if the request is a GET we return the login page
        
                return render_template('forms/login.html')
            else:  # if the request is POST the we check if the user exist and with the right password
                email = request.form.get('email')
                password = request.form.get('password')
                remember = True if request.form.get('remember') else False
                user = User.query.filter_by(email=email).first()

                if not user:
                    flash('Please sign up before!')
                    return redirect(url_for('signup'))
                elif not check_password_hash(user.password, str(password)):
                    flash('Please check your login details and try again.')
                    return redirect(url_for('login'))
                login_user(user, remember=remember)
                return redirect(url_for('account'))
        else:
            return redirect('/login')
        
    @app.route('/verify/<string:token>')
    @lr
    def verify(token: str) -> werkzeug.wrappers.response.Response:
        """
        Route to verify a user's account using a verification token.

        Args:
            token (str): The verification token.

        Returns:
            Response: A response object.
        
        """
        
        user = current_user._get_current_object()
        if type(user) is User:
            if user.verified == 1:
                print("account already verified")
            else:
                if user.verify_token == token:
                    user.verified = 1
                    db.session.commit()
                    print("account verified")
            return redirect(url_for('account'))
        else:
            return redirect(url_for('login'))
        
    @app.route('/account')
    @lr
    def account() -> str:
        """
        Renders the account page for a logged-in user.

        Returns:
            str: The rendered HTML template for the account page.
        """
        return render_template('forms/account.html',username=current_user.name,email=current_user.email)

    @app.route('/logout')
    @lr
    def logout() -> werkzeug.wrappers.response.Response:
        """
        A route function that handles the '/logout' endpoint. 
        It logs the user out by calling the `logout_user()` function and redirects the user to the 'index' page.

        Returns:
            A `werkzeug.wrappers.response.Response` object representing the HTTP response.
        """

        logout_user()
        return redirect(url_for('index'))
    return app