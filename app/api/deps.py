import os
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer()

async def get_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    """
    Authorization 헤더에서 Bearer 토큰을 추출합니다.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    expected_token = os.getenv("AUTHORIZATION_TOKEN")
    
    if not expected_token:
        # 환경 변수가 설정되어 있지 않으면 보안상 모든 요청 거부 또는 경고 후 허용 (여기서는 거부)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Authorization configuration error",
        )

    if token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return token
