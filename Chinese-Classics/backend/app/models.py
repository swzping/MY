from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(128), nullable=False)
    
    # VIP信息
    is_vip = Column(Boolean, default=False)
    vip_level = Column(String(20), default='free')  # free, monthly, yearly, lifetime
    vip_expire_at = Column(DateTime, nullable=True)
    
    # 用户信息
    nickname = Column(String(50), default='国学爱好者')
    avatar = Column(String(255), default='')
    credits = Column(Integer, default=100)
    
    # 设置
    settings = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # 关系
    histories = relationship("History", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")


class History(Base):
    __tablename__ = 'histories'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 咨询信息
    type = Column(String(50), nullable=False)  # iching, horoscope, zodiac, bazi, naming
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # 会话ID
    session_id = Column(String(100), default='default')
    
    # 元数据
    tokens_used = Column(Integer, default=0)
    duration = Column(Float, default=0.0)  # 响应时间（秒）
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="histories")


class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 报告信息
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    
    # 报告内容
    content = Column(Text, nullable=False)
    data = Column(JSON, default=dict)  # 结构化数据用于图表
    
    # 分享信息
    share_code = Column(String(20), unique=True, index=True, nullable=True)
    share_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="reports")


class Upload(Base):
    __tablename__ = 'uploads'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(50), nullable=False)
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    processed_content = Column(Text, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = 'feedbacks'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # 反馈内容
    type = Column(String(50), default='general')  # general, bug, feature, complaint
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5星评分
    
    # 联系信息（非登录用户）
    contact_email = Column(String(100), nullable=True)
    
    # 处理状态
    status = Column(String(20), default='pending')  # pending, processing, resolved
    admin_reply = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="feedbacks")


class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 评价内容
    content = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5星
    
    # 点赞数
    likes = Column(Integer, default=0)
    
    # 是否显示
    is_visible = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="reviews")


class Tutorial(Base):
    __tablename__ = 'tutorials'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 教程信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(50), default='guide')  # guide, feature, example
    
    # 排序和显示
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
