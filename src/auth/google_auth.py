from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException
import os

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is required")

def verify_google_token(token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )

        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        return idinfo

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Token verification failed")