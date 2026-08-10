from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models, schemas
from database import get_db


SECRET = "emadoofprogram"
ALGORITHM = "HS256"
EXPIRE = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str)-> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed_pass: str) -> bool:
    return pwd_context.verify(plain, hashed_pass)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> models.DBUser:
    credential_except = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate Credentails", 
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credential_except
    except JWTError:
        raise credential_except

    user = db.query(models.DBUser).filter(models.DBUser.id == int(user_id)).first()
    if user is None:
        raise credential_except

    return user
