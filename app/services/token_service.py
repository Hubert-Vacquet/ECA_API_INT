import os
import hashlib

def generate_session_token():
    return hashlib.sha256(os.urandom(32)).hexdigest()
