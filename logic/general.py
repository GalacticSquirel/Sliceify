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