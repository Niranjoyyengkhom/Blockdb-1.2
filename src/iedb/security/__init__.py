"""
IEDB Security module - JWT authentication and authorization
"""
from typing import Dict, List, Any, Optional, Union
import os
import json
import time
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from pydantic import BaseModel


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class JWTAuth:
    """JWT Authentication handler."""
    
    def __init__(
        self, 
        secret_key: str, 
        algorithm: str = "HS256", 
        token_expire_minutes: int = 30,
        users_file: str = None
    ):
        """Initialize JWT Auth handler.
        
        Args:
            secret_key: Secret key for JWT encoding/decoding
            algorithm: JWT algorithm
            token_expire_minutes: Token expiration time in minutes
            users_file: Optional path to users JSON file
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        self.users_file = users_file
        
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        
        # Initialize users if file provided
        self.users_db = {}
        if users_file and os.path.exists(users_file):
            self._load_users()
    
    def _load_users(self):
        """Load users from file."""
        try:
            with open(self.users_file, "r") as f:
                users_data = json.load(f)
                self.users_db = users_data
        except (json.JSONDecodeError, IOError):
            self.users_db = {}
    
    def _save_users(self):
        """Save users to file."""
        if not self.users_file:
            return
        
        with open(self.users_file, "w") as f:
            json.dump(self.users_db, f, indent=2)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
        
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Get password hash.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user from database.
        
        Args:
            username: Username
        
        Returns:
            User object if found, None otherwise
        """
        if username in self.users_db:
            user_data = self.users_db[username]
            return UserInDB(**user_data)
        return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user(username)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Remove hashed_password from returned user
        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled
        )
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time
        
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def add_user(self, username: str, password: str, email: str = None, full_name: str = None) -> bool:
        """Add new user.
        
        Args:
            username: Username
            password: Plain text password
            email: Optional email
            full_name: Optional full name
        
        Returns:
            True if user added, False if username already exists
        """
        if username in self.users_db:
            return False
        
        hashed_password = self.get_password_hash(password)
        
        self.users_db[username] = {
            "username": username,
            "email": email,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "disabled": False
        }
        
        self._save_users()
        return True
    
    async def get_current_user(self, token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))) -> User:
        """Get current user from token.
        
        Args:
            token: JWT token
        
        Returns:
            User object
        
        Raises:
            HTTPException: If token invalid or user not found
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
        except jwt.PyJWTError:
            raise credentials_exception
        
        user = self.get_user(username)
        if user is None:
            raise credentials_exception
        
        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled
        )
    
    def setup_routes(self, app: FastAPI):
        """Set up authentication routes on FastAPI app.
        
        Args:
            app: FastAPI application
        """
        @app.post("/token")
        async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
            user = self.authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(minutes=self.token_expire_minutes)
            access_token = self.create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )
            
            return {"access_token": access_token, "token_type": "bearer"}
        
        @app.get("/users/me", response_model=User)
        async def read_users_me(current_user: User = Depends(self.get_current_user)):
            return current_user


class SecurityManager:
    """Security manager for IEDB."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize security manager.
        
        Args:
            secret_key: Secret key for encryption/signing
        """
        if not secret_key:
            # Generate random secret key
            import secrets
            secret_key = secrets.token_hex(32)
        
        self.secret_key = secret_key
        self.jwt_auth = None
    
    def setup_jwt_auth(
        self, 
        algorithm: str = "HS256", 
        token_expire_minutes: int = 30,
        users_file: str = None
    ) -> JWTAuth:
        """Set up JWT authentication.
        
        Args:
            algorithm: JWT algorithm
            token_expire_minutes: Token expiration time in minutes
            users_file: Optional path to users JSON file
        
        Returns:
            JWTAuth instance
        """
        self.jwt_auth = JWTAuth(
            secret_key=self.secret_key,
            algorithm=algorithm,
            token_expire_minutes=token_expire_minutes,
            users_file=users_file
        )
        
        return self.jwt_auth
    
    def get_jwt_auth(self) -> JWTAuth:
        """Get JWT authentication handler.
        
        Returns:
            JWTAuth instance
        """
        if not self.jwt_auth:
            self.jwt_auth = self.setup_jwt_auth()
        
        return self.jwt_auth