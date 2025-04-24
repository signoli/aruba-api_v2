import requests
import base64
import hashlib
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

load_dotenv()

# Configuración
ARUBA_USER = os.getenv("ARUBA_USERNAME")
ARUBA_PASS = os.getenv("ARUBA_PASSWORD")
BASE_URL = 'https://sso.arubainstanton.com'
REDIRECT_URI = 'https://portal.arubainstanton.com'

# Generar Code Verifier y Code Challenge
def generate_code_verifier_and_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip("=")[:43]
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip("=")[:43]
    return code_verifier, code_challenge

# Login inicial para obtener token de sesión
def get_session_token():
    login_data = {
        'username': ARUBA_USER,
        'password': ARUBA_PASS
    }
    response = requests.post(f"{BASE_URL}/aio/api/v1/mfa/validate/full", data=login_data)
    response.raise_for_status()
    return response.json()['access_token']

# Obtener client ID desde configuración global
def get_client_id():
    response = requests.get(f"{REDIRECT_URI}/settings.json")
    response.raise_for_status()
    return response.json()['ssoClientIdAuthZ']

# Obtener Authorization Code
def get_auth_code(client_id, session_token, code_challenge):
    state = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip("=")[:43]
    params = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'profile openid',
        'state': state,
        'code_challenge_method': 'S256',
        'code_challenge': code_challenge,
        'sessionToken': session_token
    }
    response = requests.get(f"{BASE_URL}/as/authorization.oauth2", params=params, allow_redirects=False)
    response.raise_for_status()
    redirect_url = response.headers.get('Location')
    query_params = parse_qs(urlparse(redirect_url).query)
    return query_params['code'][0]

# Obtener Bearer Token
def get_bearer_token(client_id, auth_code, code_verifier):
    token_data = {
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'code': auth_code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code'
    }
    response = requests.post(f"{BASE_URL}/as/token.oauth2", data=token_data)
    response.raise_for_status()
    return response.json()['access_token']

# Flujo principal
def get_token():
    code_verifier, code_challenge = generate_code_verifier_and_challenge()
    session_token = get_session_token()
    client_id = get_client_id()
    auth_code = get_auth_code(client_id, session_token, code_challenge)
    return get_bearer_token(client_id, auth_code, code_verifier)
