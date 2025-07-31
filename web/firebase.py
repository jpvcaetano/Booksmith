"""
Firebase Authentication and User Management for Booksmith.
Split into client-side authentication and server-side user management for clean separation of concerns.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, auth
from pydantic import BaseModel, EmailStr, Field
import pyrebase

logger = logging.getLogger(__name__)


# Pydantic Models
class FirebaseUser(BaseModel):
    """Pydantic model for Firebase user data."""
    uid: str
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    email_verified: Optional[bool] = None
    phone_number: Optional[str] = None
    photo_url: Optional[str] = None
    password: Optional[str] = None
    disabled: Optional[bool] = None
    creation_timestamp: Optional[datetime] = None
    last_sign_in_timestamp: Optional[datetime] = None

    @classmethod
    def from_firebase_user(cls, firebase_user: auth.UserRecord) -> "FirebaseUser":
        """Create a FirebaseUser from Firebase UserRecord."""
        return cls(
            uid=firebase_user.uid,
            display_name=firebase_user.display_name,
            email=firebase_user.email,
            email_verified=firebase_user.email_verified,
            phone_number=firebase_user.phone_number,
            photo_url=firebase_user.photo_url,
            disabled=firebase_user.disabled,    
            creation_timestamp=datetime.fromtimestamp(firebase_user.user_metadata.creation_timestamp / 1000) if firebase_user.user_metadata.creation_timestamp else None,
            last_sign_in_timestamp=datetime.fromtimestamp(firebase_user.user_metadata.last_sign_in_timestamp / 1000) if firebase_user.user_metadata.last_sign_in_timestamp else None,
        )


class FirebaseAuth:
    """
    Client-side Firebase Authentication using pyrebase4.
    Handles login, registration, and password verification.
    """
    
    def __init__(self, project_id: str):
        """
        Initialize Firebase Authentication.
        
        Args:
            project_id: Firebase project ID
        """
        self.project_id = project_id
        self.client_auth = None
        self.firebase_config = None
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup pyrebase4 for client-side authentication."""
        try:
            # Get Firebase web config from environment variables
            self.firebase_config = {
                "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
                "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", ""),
                "projectId": self.project_id,
                "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", ""),
                "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", ""),
                "appId": os.environ.get("FIREBASE_APP_ID", ""),
                "databaseURL": "" # Not needed for auth
            }
            
            # Check if we have required config
            if self.firebase_config["apiKey"] and self.firebase_config["authDomain"]:
                firebase_client = pyrebase.initialize_app(self.firebase_config)
                self.client_auth = firebase_client.auth()
                logger.info("✅ Firebase Authentication (pyrebase4) initialized")
            else:
                logger.warning("⚠️ Firebase web config incomplete - authentication not available")
                logger.info("Set FIREBASE_API_KEY and FIREBASE_AUTH_DOMAIN for authentication")
                
        except Exception as e:
            logger.error(f"Failed to setup Firebase authentication: {e}")
    
    def is_available(self) -> bool:
        """Check if authentication is available."""
        return self.client_auth is not None
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Dict with success status, user data, and token
        """
        if not self.client_auth:
            return {
                "success": False,
                "error": "Authentication not available. Please check Firebase configuration."
            }
        
        try:
            # Login with pyrebase4
            user = self.client_auth.sign_in_with_email_and_password(email, password)
            
            # Get user info from Firebase Admin SDK for additional details
            try:
                admin_user = auth.get_user(user['localId'])
                display_name = admin_user.display_name or email.split('@')[0]
                email_verified = admin_user.email_verified
            except:
                # Fallback if admin lookup fails
                display_name = email.split('@')[0]
                email_verified = False
            
            return {
                "success": True,
                "user": {
                    "uid": user['localId'],
                    "email": user['email'],
                    "display_name": display_name,
                    "email_verified": email_verified
                },
                "token": user['idToken']
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def register(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """
        Register new user with email and password.
        
        Args:
            email: User email
            password: User password
            display_name: Optional display name
            
        Returns:
            Dict with success status, user data, and token
        """
        if not self.client_auth:
            return {
                "success": False,
                "error": "Authentication not available. Please check Firebase configuration."
            }
        
        try:
            # Create user with pyrebase4
            user = self.client_auth.create_user_with_email_and_password(email, password)
            
            # Update display name using Firebase Admin SDK if provided
            if display_name:
                try:
                    auth.update_user(user['localId'], display_name=display_name)
                except Exception as e:
                    logger.warning(f"Failed to update display name: {e}")
            
            return {
                "success": True,
                "user": {
                    "uid": user['localId'],
                    "email": user['email'],
                    "display_name": display_name or email.split('@')[0],
                    "email_verified": False
                },
                "token": user['idToken']
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    

    
    def get_status(self) -> Dict[str, Any]:
        """Get authentication status."""
        return {
            "available": self.is_available(),
            "project_id": self.project_id,
            "config_complete": bool(self.firebase_config and 
                                   self.firebase_config.get("apiKey") and 
                                   self.firebase_config.get("authDomain")),
            "status": "✅ Ready" if self.is_available() else "❌ Not configured"
        }


class FirebaseUserManager:
    """
    Server-side Firebase User Management using firebase-admin.
    Handles user CRUD operations and administrative tasks.
    """
    
    def __init__(self):
        """Initialize Firebase User Manager."""
        self.is_initialized = False
        self.project_id = None
    
    def initialize(self, service_account_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK.
        
        Args:
            service_account_path: Optional path to service account key file.
                                If not provided, will try environment variables.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Check if Firebase is already initialized
            try:
                app = firebase_admin.get_app()
                logger.info("Firebase Admin SDK already initialized")
                self.is_initialized = True
                self.project_id = getattr(app, 'project_id', 'Unknown')
                return True
            except ValueError:
                # App doesn't exist, need to create it
                pass
            
            # Get service account path
            env_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
            if service_account_path:
                env_path = service_account_path
            elif env_path:
                # Handle relative paths
                if not os.path.isabs(env_path):
                    project_root = Path(__file__).parent.parent
                    env_path = str(project_root / env_path)
            
            if env_path and os.path.exists(env_path):
                logger.info(f"Initializing Firebase Admin SDK with: {env_path}")
                cred = credentials.Certificate(env_path)
                app = firebase_admin.initialize_app(cred)
                self.is_initialized = True
                self.project_id = getattr(app, 'project_id', 'Unknown')
                logger.info("✅ Firebase Admin SDK initialized successfully!")
                return True
            else:
                logger.error(f"Service account key file not found: {env_path}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Firebase Admin SDK initialization error: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[FirebaseUser]:
        """Get a user by UID."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            firebase_user = auth.get_user(user_id)
            logger.info(f'Successfully fetched user data for UID: {firebase_user.uid}')
            return FirebaseUser.from_firebase_user(firebase_user)
        except Exception as e:
            logger.error(f"Unexpected error fetching user {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[FirebaseUser]:
        """Get a user by email address."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            firebase_user = auth.get_user_by_email(email)
            logger.info(f'Successfully fetched user data for email: {email}')
            return FirebaseUser.from_firebase_user(firebase_user)
        except Exception as e:
            logger.error(f"Unexpected error fetching user by email {email}: {e}")
            return None
    
    def create_user(self, user_data: FirebaseUser) -> Optional[FirebaseUser]:
        """Create a new user."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            firebase_user = auth.create_user(**user_data.model_dump(exclude_none=True))
            logger.info(f'Successfully created new user: {firebase_user.uid}')
            return FirebaseUser.from_firebase_user(firebase_user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def update_user(self, user_id: str, user_data: FirebaseUser) -> Optional[FirebaseUser]:
        """Update an existing user."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            firebase_user = auth.update_user(user_id, **user_data.model_dump(exclude_none=True))
            logger.info(f'Successfully updated user: {firebase_user.uid}')
            return FirebaseUser.from_firebase_user(firebase_user)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return False
        
        try:
            auth.delete_user(user_id)
            logger.info(f'Successfully deleted user: {user_id}')
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    def list_users(self, max_results: int = 1000) -> List[FirebaseUser]:
        """List all users."""
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return []
        
        try:
            users = []
            page = auth.list_users(max_results=max_results)
            
            for firebase_user in page.users:
                users.append(FirebaseUser.from_firebase_user(firebase_user))
            
            logger.info(f'Successfully listed {len(users)} users')
            return users
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test Firebase connection."""
        if not self.is_initialized:
            return False
        
        try:
            # Try to list users (limit to 1 to test connection)
            auth.list_users(max_results=1)
            logger.info("✅ Firebase connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Firebase connection test failed: {e}")
            return False
    
    def verify_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Firebase ID token.
        
        Args:
            id_token: The Firebase ID token to verify
            
        Returns:
            Decoded token data if valid, None otherwise
        """
        if not self.is_initialized:
            logger.error("Firebase not initialized")
            return None
        
        try:
            # Use firebase-admin to verify token
            decoded_token = auth.verify_id_token(id_token)
            logger.info(f"Successfully verified token for user: {decoded_token['uid']}")
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying ID token: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get Firebase Admin SDK status."""
        return {
            "initialized": self.is_initialized,
            "project_id": self.project_id,
            "connection_ok": self.test_connection() if self.is_initialized else False,
            "status": "✅ Connected" if self.is_initialized else "❌ Not initialized"
        }
