from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.api.endpoints.auth import get_current_active_user
from app.db import get_db
from app.models import User, History, Report

router = APIRouter()

# Pydantic Models
class HistoryCreate(BaseModel):
    type: str
    question: str
    answer: str
    session_id: Optional[str] = "default"
    tokens_used: Optional[int] = 0
    duration: Optional[float] = 0.0

class HistoryResponse(BaseModel):
    id: int
    type: str
    question: str
    answer: str
    created_at: datetime
    session_id: str

class ReportCreate(BaseModel):
    title: str
    type: str
    content: str
    data: Optional[dict] = None

class ReportResponse(BaseModel):
    id: int
    title: str
    type: str
    content: str
    data: Optional[dict]
    share_code: Optional[str]
    share_count: int
    created_at: datetime

# 历史记录API
@router.get("/histories", response_model=List[HistoryResponse])
async def get_histories(
    type: Optional[str] = Query(None, description="筛选类型: iching, horoscope, zodiac, bazi, naming"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取历史记录列表"""
    # 构建查询
    query = select(History).where(History.user_id == current_user.id)
    
    # 类型筛选
    if type:
        query = query.where(History.type == type)
    
    # 搜索
    if search:
        query = query.where(
            (History.question.contains(search)) | 
            (History.answer.contains(search))
        )
    
    # 排序和分页
    query = query.order_by(desc(History.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    histories = result.scalars().all()
    
    return histories

@router.get("/histories/{history_id}", response_model=HistoryResponse)
async def get_history(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单条历史记录"""
    result = await db.execute(
        select(History).where(
            History.id == history_id,
            History.user_id == current_user.id
        )
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    return history

@router.post("/histories", response_model=HistoryResponse)
async def create_history(
    history_in: HistoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建历史记录"""
    history = History(
        user_id=current_user.id,
        type=history_in.type,
        question=history_in.question,
        answer=history_in.answer,
        session_id=history_in.session_id,
        tokens_used=history_in.tokens_used,
        duration=history_in.duration
    )
    
    db.add(history)
    await db.commit()
    await db.refresh(history)
    
    return history

@router.delete("/histories/{history_id}")
async def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除历史记录"""
    result = await db.execute(
        select(History).where(
            History.id == history_id,
            History.user_id == current_user.id
        )
    )
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    
    await db.delete(history)
    await db.commit()
    
    return {"message": "历史记录已删除"}

@router.get("/histories/stats/overview")
async def get_history_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取历史记录统计"""
    # 总记录数
    total_result = await db.execute(
        select(func.count(History.id)).where(History.user_id == current_user.id)
    )
    total = total_result.scalar()
    
    # 各类型统计
    type_stats_result = await db.execute(
        select(History.type, func.count(History.id))
        .where(History.user_id == current_user.id)
        .group_by(History.type)
    )
    type_stats = {row[0]: row[1] for row in type_stats_result.all()}
    
    # 本月记录数
    from datetime import datetime, timedelta
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_result = await db.execute(
        select(func.count(History.id))
        .where(History.user_id == current_user.id)
        .where(History.created_at >= month_start)
    )
    month_count = month_result.scalar()
    
    return {
        "total": total,
        "month_count": month_count,
        "type_distribution": type_stats,
        "favorite_type": max(type_stats, key=type_stats.get) if type_stats else None
    }

# 报告API
@router.get("/reports", response_model=List[ReportResponse])
async def get_reports(
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取报告列表"""
    query = select(Report).where(Report.user_id == current_user.id)
    
    if type:
        query = query.where(Report.type == type)
    
    query = query.order_by(desc(Report.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return reports

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取单条报告"""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return report

@router.post("/reports", response_model=ReportResponse)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建报告"""
    import secrets
    
    report = Report(
        user_id=current_user.id,
        title=report_in.title,
        type=report_in.type,
        content=report_in.content,
        data=report_in.data or {},
        share_code=secrets.token_urlsafe(12)[:16]  # 生成分享码
    )
    
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return report

@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除报告"""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    await db.delete(report)
    await db.commit()
    
    return {"message": "报告已删除"}

# 分享功能
@router.get("/share/{share_code}")
async def get_shared_report(
    share_code: str,
    db: AsyncSession = Depends(get_db)
):
    """通过分享码获取报告（公开访问）"""
    result = await db.execute(
        select(Report).where(Report.share_code == share_code)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="分享链接无效或已过期")
    
    # 增加分享计数
    report.share_count += 1
    await db.commit()
    
    return {
        "title": report.title,
        "type": report.type,
        "content": report.content,
        "data": report.data,
        "created_at": report.created_at,
        "author_nickname": report.user.nickname if report.user else "匿名"
    }

@router.post("/reports/{report_id}/share")
async def generate_share_code(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成分享码"""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    if not report.share_code:
        import secrets
        report.share_code = secrets.token_urlsafe(12)[:16]
        await db.commit()
    
    return {
        "share_code": report.share_code,
        "share_url": f"/share/{report.share_code}"
    }
