from imports import *

api_key = os.environ.get('API_KEY')
def send_verify_email(link: str, email: str) -> None:
    # set up the SMTP server
    server = smtplib.SMTP('smtp.eu.mailgun.org', 25)
    server.starttls()

    # Login Credentials for sending the mail
    server.login("postmaster@mg.sliceify.co.uk", str(api_key)) # use "heroku config:set API_KEY=" to change

    # create the email
    msg = MIMEMultipart()
    msg['From'] = "Sliceify <Sliceify-Verify@sliceify.co.uk>"
    msg['To'] = email
    msg['Subject'] = "Verify Your Slicify Account"
    message = f"Follow this link to verify your account: {link}"
    msg.attach(MIMEText(message))

    server.send_message(msg)
    server.quit()
    

def lr(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return render_template('errors/auth.html')
        return f(*args, **kwargs)
    return decorated_function

def job_belongs_to_user(f):
    @wraps(f)
    def decorated_function(job_name, *args, **kwargs):
        if not current_user.is_authenticated:
            return render_template('errors/auth.html')
        if job_name not in current_user.jobs:
            print(job_name, current_user.jobs)
            return render_template('errors/not_your_job.html')
        return f(job_name, *args, **kwargs)
    return decorated_function

def password_check(password: str) -> bool:
        """
        Check if a password meets the following criteria:
        - Contains at least 8 characters
        - Contains at least one lowercase letter
        - Contains at least one uppercase letter
        - Contains at least one digit
        - Contains at least one special character

        Args:
            password (str): The password to be checked.

        Returns:
            bool: True if the password meets the criteria, False otherwise.
        """
        l, u, p, d = 0, 0, 0, 0
        special = ["!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/",
                    ":", ";", "<", "=", ">", "?", "@", "[", "]", "^", "_", "`", "{", "|", "}", "~"]
        s = str(password)
        if s == "":
            return False
        if s == None:
            return False
        if (len(s) >= 8):
            for i in s:
                if (i.islower()):
                    l += 1
                if (i.isupper()):
                    u += 1
                if (i.isdigit()):
                    d += 1
                if i in special:
                    p += 1
        if not (l >= 1 and u >= 1 and p >= 1 and d >= 1 and l+p+u+d == len(s)):
            return False
        return True