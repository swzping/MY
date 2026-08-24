from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from app.core import security
from app.db import get_db
from app.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    nickname: str
    is_vip: bool
    vip_level: str
    credits: int
    avatar: Optional[str]
    created_at: datetime

class UserProfile(UserResponse):
    histories_count: int
    reports_count: int

# 依赖函数
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = security.jwt.decode(token, security.settings.SECRET_KEY, algorithms=[security.settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user

# 路由
@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被注册"
        )
    
    # 检查邮箱是否已存在
    if user_in.email:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 创建新用户
    hashed_password = security.get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        hashed_password=hashed_password,
        email=user_in.email,
        phone=user_in.phone,
        nickname=user_in.nickname or user_in.username,
        credits=100,  # 新用户赠送100积分
        is_vip=False,
        vip_level='free'
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 生成token
    access_token = security.create_access_token(subject=user.username)
    expires_in = security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "is_vip": user.is_vip,
            "credits": user.credits
        }
    }

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # 生成token
    access_token = security.create_access_token(subject=user.username)
    expires_in = security.settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "is_vip": user.is_vip,
            "vip_level": user.vip_level,
            "credits": user.credits,
            "avatar": user.avatar
        }
    }

@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    # 计算历史记录和报告数量
    histories_count = len(current_user.histories) if current_user.histories else 0
    reports_count = len(current_user.reports) if current_user.reports else 0
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "nickname": current_user.nickname,
        "is_vip": current_user.is_vip,
        "vip_level": current_user.vip_level,
        "credits": current_user.credits,
        "avatar": current_user.avatar,
        "created_at": current_user.created_at,
        "histories_count": histories_count,
        "reports_count": reports_count
    }

@router.put("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    if user_update.nickname:
        current_user.nickname = user_update.nickname
    if user_update.email:
        current_user.email = user_update.email
    if user_update.avatar:
        current_user.avatar = user_update.avatar
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return current_user

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    if not security.verify_password(old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    current_user.hashed_password = security.get_password_hash(new_password)
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "密码修改成功"}

# VIP相关
@router.get("/vip/status")
async def get_vip_status(current_user: User = Depends(get_current_active_user)):
    """获取VIP状态"""
    return {
        "is_vip": current_user.is_vip,
        "vip_level": current_user.vip_level,
        "vip_expire_at": current_user.vip_expire_at,
        "credits": current_user.credits,
        "benefits": {
            "free": {
                "daily_limit": 10,
                "features": ["基础命理咨询", "历史记录查看"]
            },
            "monthly": {
                "daily_limit": 100,
                "features": ["高级命理分析", "详细报告", "优先服务", "无限历史记录"]
            },
            "yearly": {
                "daily_limit": -1,  # 无限制
                "features": ["专家咨询", "专属客服", "所有高级功能", "导出报告"]
            }
        }
    }

@router.post("/vip/upgrade")
async def upgrade_vip(
    level: str,  # monthly, yearly, lifetime
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """升级VIP（模拟支付）"""
    prices = {
        "monthly": 29.9,
        "yearly": 299.0,
        "lifetime": 999.0
    }
    
    if level not in prices:
        raise HTTPException(status_code=400, detail="无效的VIP等级")
    
    # 模拟支付成功，直接升级
    current_user.is_vip = True
    current_user.vip_level = level
    
    if level == "monthly":
        current_user.vip_expire_at = datetime.utcnow() + timedelta(days=30)
    elif level == "yearly":
        current_user.vip_expire_at = datetime.utcnow() + timedelta(days=365)
    elif level == "lifetime":
        current_user.vip_expire_at = None  # 永久
    
    await db.commit()
    
    return {
        "message": f"已成功升级至{level}会员",
        "price": prices[level],
        "expire_at": current_user.vip_expire_at
    }
