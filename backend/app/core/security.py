"""
作者：Zxy
"""
# backend/app/core/security.py

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# 1. 配置参数 (真实项目中这些应该放在 .env 文件里)
SECRET_KEY = "CHANGE_THIS_TO_A_SUPER_SECRET_KEY"  # 密钥，切记不要泄露
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # token 有效期 30 天

# 2. 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 3. 函数：验证密码 (明文 vs 密文)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# 4. 函数：获取密码的哈希值 (加密)
def get_password_hash(password):
    return pwd_context.hash(password)


# 5. 函数：生成 JWT 令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # 把过期时间写进令牌
    to_encode.update({"exp": expire})
    # 生成加密字符串
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt