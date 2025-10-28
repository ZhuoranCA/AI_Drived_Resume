# utils/auth_handler.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "super_secret_key_please_change"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Generate JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # contains user_id, email, role
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


# --- NEW: Extract current user info ---
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials)
    return payload


# --- NEW: Role-based access control ---
def require_role(required_role: str):
    def role_checker(user_data: dict = Depends(get_current_user)):
        if user_data.get("role") != required_role:
            raise HTTPException(status_code=403, detail="Access denied. Insufficient role.")
        return user_data
    return role_checker
