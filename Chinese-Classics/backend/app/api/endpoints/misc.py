from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid

from app.api.endpoints.auth import get_current_active_user, get_current_user
from app.db import get_db
from app.models import User, Upload, Feedback, Review, Tutorial

router = APIRouter()

# 确保上传目录存在
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic Models
class FeedbackCreate(BaseModel):
    type: str = "general"  # general, bug, feature, complaint
    content: str
    rating: Optional[int] = None
    contact_email: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    type: str
    content: str
    rating: Optional[int]
    status: str
    created_at: datetime

class ReviewCreate(BaseModel):
    content: str
    rating: int  # 1-5

class ReviewResponse(BaseModel):
    id: int
    content: str
    rating: int
    likes: int
    created_at: datetime
    user_nickname: str

# 文件上传API
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传文件"""
    # 检查文件类型
    allowed_types = ['text/plain', 'application/pdf', 'text/markdown', 'application/msword']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 创建数据库记录
    upload = Upload(
        user_id=current_user.id if current_user else None,
        filename=unique_filename,
        original_name=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file.content_type,
        status='pending'
    )
    
    db.add(upload)
    await db.commit()
    await db.refresh(upload)
    
    # 这里可以添加文件内容解析逻辑
    # 例如：解析PDF、提取文本等
    
    return {
        "id": upload.id,
        "filename": upload.original_name,
        "size": upload.file_size,
        "status": upload.status,
        "message": "文件上传成功，正在处理中..."
    }

@router.get("/uploads")
async def get_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取上传文件列表"""
    query = select(Upload).where(Upload.user_id == current_user.id)
    query = query.order_by(desc(Upload.uploaded_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    uploads = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "filename": u.original_name,
            "size": u.file_size,
            "status": u.status,
            "uploaded_at": u.uploaded_at
        }
        for u in uploads
    ]

# 反馈API
@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(
    feedback_in: FeedbackCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交反馈"""
    feedback = Feedback(
        user_id=current_user.id if current_user else None,
        type=feedback_in.type,
        content=feedback_in.content,
        rating=feedback_in.rating,
        contact_email=feedback_in.contact_email or (current_user.email if current_user else None),
        status='pending'
    )
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    return feedback

@router.get("/feedback/my", response_model=List[FeedbackResponse])
async def get_my_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取我的反馈列表"""
    query = select(Feedback).where(Feedback.user_id == current_user.id)
    query = query.order_by(desc(Feedback.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    feedbacks = result.scalars().all()
    
    return feedbacks

# 评价API
@router.post("/reviews", response_model=ReviewResponse)
async def create_review(
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建评价"""
    if review_in.rating < 1 or review_in.rating > 5:
        raise HTTPException(status_code=400, detail="评分必须在1-5之间")
    
    review = Review(
        user_id=current_user.id,
        content=review_in.content,
        rating=review_in.rating,
        likes=0,
        is_visible=True
    )
    
    db.add(review)
    await db.commit()
    await db.refresh(review)
    
    return {
        "id": review.id,
        "content": review.content,
        "rating": review.rating,
        "likes": review.likes,
        "created_at": review.created_at,
        "user_nickname": current_user.nickname
    }

@router.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取评价列表（公开）"""
    query = select(Review).where(Review.is_visible == True)
    query = query.order_by(desc(Review.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "content": r.content,
            "rating": r.rating,
            "likes": r.likes,
            "created_at": r.created_at,
            "user_nickname": r.user.nickname if r.user else "匿名用户"
        }
        for r in reviews
    ]

@router.post("/reviews/{review_id}/like")
async def like_review(
    review_id: int,
    db: AsyncSession = Depends(get_db)
):
    """点赞评价"""
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(status_code=404, detail="评价不存在")
    
    review.likes += 1
    await db.commit()
    
    return {"message": "点赞成功", "likes": review.likes}

# 教程API
@router.get("/tutorials")
async def get_tutorials(
    type: Optional[str] = Query(None, description="教程类型: guide, feature, example"),
    db: AsyncSession = Depends(get_db)
):
    """获取教程列表"""
    query = select(Tutorial).where(Tutorial.is_active == True)
    
    if type:
        query = query.where(Tutorial.type == type)
    
    query = query.order_by(Tutorial.sort_order)
    
    result = await db.execute(query)
    tutorials = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "title": t.title,
            "content": t.content,
            "type": t.type
        }
        for t in tutorials
    ]

@router.get("/tutorials/{tutorial_id}")
async def get_tutorial(
    tutorial_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取单个教程"""
    result = await db.execute(
        select(Tutorial).where(
            Tutorial.id == tutorial_id,
            Tutorial.is_active == True
        )
    )
    tutorial = result.scalar_one_or_none()
    
    if not tutorial:
        raise HTTPException(status_code=404, detail="教程不存在")
    
    return {
        "id": tutorial.id,
        "title": tutorial.title,
        "content": tutorial.content,
        "type": tutorial.type
    }

# 初始化教程数据
async def init_tutorials(db: AsyncSession):
    """初始化新手教程数据"""
    result = await db.execute(select(func.count(Tutorial.id)))
    count = result.scalar()
    
    if count == 0:
        tutorials = [
            Tutorial(
                title="欢迎使用国学命理",
                content="""
# 欢迎使用国学命理智能体

## 快速开始

1. **选择功能**：在首页点击您感兴趣的功能模块
2. **开始咨询**：在对话框中输入您的问题
3. **查看报告**：咨询完成后可以生成详细报告

## 五大核心功能

- **周易占卜**：六爻排盘，解析吉凶祸福
- **星座运势**：星象奥秘，每日运势更新
- **生肖配对**：传统合婚，分析性格匹配
- **八字命理**：四柱排盘，详批流年大运
- **起名建议**：五行八字，定制吉祥好名

## 会员权益

- **免费用户**：每日10次咨询额度
- **月度会员**：每日100次咨询，详细报告
- **年度会员**：无限咨询，专家服务

祝您使用愉快！
                """,
                type="guide",
                sort_order=1
            ),
            Tutorial(
                title="如何进行周易占卜",
                content="""
# 周易占卜指南

## 占卜流程

1. **静心凝神**：在心中默念您要询问的事情
2. **选择类型**：点击首页的"周易占卜"
3. **描述问题**：详细描述您想咨询的问题
4. **等待解析**：AI将为您进行六爻排盘和解析

## 注意事项

- 同一问题不宜频繁占卜
- 问题越具体，解答越准确
- 保持开放和理性的心态

## 示例问题

- "最近工作调动是否顺利？"
- "这个项目的前景如何？"
- "和某人的合作关系会怎样？"
                """,
                type="feature",
                sort_order=2
            ),
            Tutorial(
                title="八字命理入门",
                content="""
# 八字命理入门

## 什么是八字

八字，又称四柱，是根据出生年、月、日、时的天干地支推算的命理体系。

## 如何查看

1. 点击"八字命理"功能
2. 输入您的出生时间（阳历）
3. 系统将自动排盘并分析

## 分析内容

- **五行分布**：金木水火土的强弱
- **十神关系**：比肩、劫财、食神等
- **大运流年**：人生各阶段运势
- **性格特点**：基于八字的性格分析

## 使用建议

八字命理是传统文化的一部分，请理性看待，作为人生参考。
                """,
                type="feature",
                sort_order=3
            )
        ]
        
        for tutorial in tutorials:
            db.add(tutorial)
        
        await db.commit()
