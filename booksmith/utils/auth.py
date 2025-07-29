import firebase_admin
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Extract and verify Firebase user from JWT token."""
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        user_id = decoded_token["uid"]
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid authentication credentials: {str(e)}"
        )
