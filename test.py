from imports import *
import pyotp

# Generate a secret key for a user
secret_key = pyotp.random_base32()
print(f"Secret key for user: {secret_key}")

# Generate a provisioning URI for the user to scan with their 2FA app
uri = pyotp.totp.TOTP(secret_key).provisioning_uri(name='user@example.com', issuer_name='YourApp')
print(f"Provisioning URI for user to scan: {uri}")

# Later, verify a user's 2FA code
user_code = input("Enter your 2FA code: ")
valid = pyotp.totp.TOTP(secret_key).verify(user_code)
if valid:
    print("2FA code is valid")
else:
    print("2FA code is invalid")
