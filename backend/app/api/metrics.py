"""
API endpoints для работы с метриками
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.models import Master, Employee, Administrator

logger = logging.getLogger(__name__)
from app.monitoring.metrics import (
    metrics_collector,
    performance_collector,
    business_collector,
    MetricType
)
from app.monitoring.prometheus_metrics import get_metrics, get_metrics_content_type
from typing import Union

# Тип для пользователя (может быть Master, Employee или Administrator)
UserType = Union[Master, Employee, Administrator]

def is_admin(user: UserType) -> bool:
    """Проверка, является ли пользователь администратором"""
    return isinstance(user, Administrator)

router = APIRouter(prefix="/metrics", tags=["metrics"])


class MetricResponse(BaseModel):
    """Ответ с метрикой"""
    name: str
    type: str
    description: str
    unit: str
    latest_value: Optional[float]
    count: int
    statistics: Dict[str, Any]


class MetricValueResponse(BaseModel):
    """Ответ со значением метрики"""
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metadata: Dict[str, Any]


class MetricsOverviewResponse(BaseModel):
    """Общий обзор метрик"""
    total_metrics: int
    business_metrics: int
    performance_metrics: int
    active_metrics: int
    last_updated: datetime


class BusinessMetricsResponse(BaseModel):
    """Ответ с бизнес-метриками"""
    requests_total: Optional[float]
    requests_by_status: Dict[str, float]
    requests_by_city: Dict[str, float]
    transactions_total: Optional[float]
    transactions_amount: Optional[float]
    active_users: Optional[float]
    conversion_rate: Optional[float]
    avg_processing_time: Optional[float]
    revenue_daily: Optional[float]
    calls_total: Optional[float]
    call_duration_avg: Optional[float]


class PerformanceMetricsResponse(BaseModel):
    """Ответ с метриками производительности"""
    http_requests_total: Optional[float]
    db_queries_total: Optional[float]
    memory_usage: Optional[float]
    cpu_usage: Optional[float]
    error_rate: Optional[float]
    cache_hits: Optional[float]
    cache_misses: Optional[float]
    db_connections_active: Optional[float]


@router.get("/", response_model=Dict[str, MetricResponse])
async def get_all_metrics(
    current_user: UserType = Depends(get_current_user)
):
    """Получение всех метрик"""
    all_metrics = metrics_collector.get_all_metrics()
    
    result = {}
    for name, data in all_metrics.items():
        definition = data.get("definition")
        if definition:
            result[name] = MetricResponse(
                name=name,
                type=definition.type.value,
                description=definition.description,
                unit=definition.unit,
                latest_value=data.get("latest_value"),
                count=data.get("count", 0),
                statistics=data.get("statistics", {})
            )
    
    return result


@router.get("/overview", response_model=MetricsOverviewResponse)
async def get_metrics_overview(
    current_user: UserType = Depends(get_current_user)
):
    """Получение общего обзора метрик"""
    all_metrics = metrics_collector.get_all_metrics()
    
    business_metrics_count = 0
    performance_metrics_count = 0
    active_metrics_count = 0
    
    for name, data in all_metrics.items():
        definition = data.get("definition")
        if definition:
            if definition.type == MetricType.BUSINESS:
                business_metrics_count += 1
            else:
                performance_metrics_count += 1
            
            if data.get("latest_value") is not None:
                active_metrics_count += 1
    
    return MetricsOverviewResponse(
        total_metrics=len(all_metrics),
        business_metrics=business_metrics_count,
        performance_metrics=performance_metrics_count,
        active_metrics=active_metrics_count,
        last_updated=datetime.utcnow()
    )


@router.get("/business", response_model=BusinessMetricsResponse)
async def get_business_metrics(
    current_user: UserType = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение бизнес-метрик"""
    # Обновляем бизнес-метрики
    await business_collector.collect_all_business_metrics(db)
    
    # Собираем метрики по статусам
    requests_by_status = {}
    status_metrics = metrics_collector.get_values("requests_by_status")
    for metric in status_metrics:
        if metric.tags.get("status"):
            requests_by_status[metric.tags["status"]] = metric.value
    
    # Собираем метрики по городам
    requests_by_city = {}
    city_metrics = metrics_collector.get_values("requests_by_city")
    for metric in city_metrics:
        if metric.tags.get("city"):
            requests_by_city[metric.tags["city"]] = metric.value
    
    return BusinessMetricsResponse(
        requests_total=metrics_collector.get_latest_value("requests_total"),
        requests_by_status=requests_by_status,
        requests_by_city=requests_by_city,
        transactions_total=metrics_collector.get_latest_value("transactions_total"),
        transactions_amount=metrics_collector.get_latest_value("transactions_amount"),
        active_users=metrics_collector.get_latest_value("active_users"),
        conversion_rate=metrics_collector.get_latest_value("conversion_rate"),
        avg_processing_time=metrics_collector.get_latest_value("avg_processing_time"),
        revenue_daily=metrics_collector.get_latest_value("revenue_daily"),
        calls_total=metrics_collector.get_latest_value("calls_total"),
        call_duration_avg=metrics_collector.get_latest_value("call_duration_avg")
    )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    current_user: UserType = Depends(get_current_user)
):
    """Получение метрик производительности"""
    # Обновляем системные метрики
    performance_collector.record_system_metrics()
    
    # Вычисляем коэффициент попаданий в кэш
    cache_hits = metrics_collector.get_latest_value("cache_hits") or 0
    cache_misses = metrics_collector.get_latest_value("cache_misses") or 0
    
    return PerformanceMetricsResponse(
        http_requests_total=metrics_collector.get_latest_value("http_requests_total"),
        db_queries_total=metrics_collector.get_latest_value("db_queries_total"),
        memory_usage=metrics_collector.get_latest_value("memory_usage"),
        cpu_usage=metrics_collector.get_latest_value("cpu_usage"),
        error_rate=metrics_collector.get_latest_value("error_rate"),
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        db_connections_active=metrics_collector.get_latest_value("db_connections_active")
    )


@router.get("/{metric_name}", response_model=MetricResponse)
async def get_metric(
    metric_name: str,
    current_user: UserType = Depends(get_current_user)
):
    """Получение конкретной метрики"""
    all_metrics = metrics_collector.get_all_metrics()
    
    if metric_name not in all_metrics:
        raise HTTPException(status_code=404, detail="Metric not found")
    
    data = all_metrics[metric_name]
    definition = data.get("definition")
    
    if not definition:
        raise HTTPException(status_code=404, detail="Metric definition not found")
    
    return MetricResponse(
        name=metric_name,
        type=definition.type.value,
        description=definition.description,
        unit=definition.unit,
        latest_value=data.get("latest_value"),
        count=data.get("count", 0),
        statistics=data.get("statistics", {})
    )


@router.get("/{metric_name}/values", response_model=List[MetricValueResponse])
async def get_metric_values(
    metric_name: str,
    current_user: UserType = Depends(get_current_user),
    since: Optional[datetime] = Query(None, description="Получить значения с этого времени"),
    limit: Optional[int] = Query(100, description="Максимальное количество значений")
):
    """Получение значений метрики"""
    values = metrics_collector.get_values(metric_name, since, limit)
    
    return [
        MetricValueResponse(
            value=value.value,
            timestamp=value.timestamp,
            tags=value.tags,
            metadata=value.metadata
        )
        for value in values
    ]


@router.get("/{metric_name}/statistics")
async def get_metric_statistics(
    metric_name: str,
    current_user: UserType = Depends(get_current_user),
    since: Optional[datetime] = Query(None, description="Получить статистику с этого времени")
):
    """Получение статистики по метрике"""
    statistics = metrics_collector.get_statistics(metric_name, since)
    
    if not statistics:
        raise HTTPException(status_code=404, detail="No data found for metric")
    
    return statistics


@router.post("/{metric_name}/record")
async def record_metric_value(
    metric_name: str,
    value: float,
    current_user: UserType = Depends(get_current_user),
    tags: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Запись значения метрики"""
    metrics_collector.record(metric_name, value, tags, metadata)
    
    return {"message": "Metric recorded successfully"}


@router.delete("/{metric_name}/clear")
async def clear_metric(
    metric_name: str,
    current_user: UserType = Depends(get_current_user)
):
    """Очистка метрики"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    with metrics_collector._lock:
        if metric_name in metrics_collector.metrics:
            metrics_collector.metrics[metric_name].clear()
            return {"message": f"Metric {metric_name} cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Metric not found")


@router.post("/collect/business")
async def collect_business_metrics(
    current_user: UserType = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Принудительный сбор бизнес-метрик"""
    await business_collector.collect_all_business_metrics(db)
    return {"message": "Business metrics collected successfully"}


@router.post("/collect/performance")
async def collect_performance_metrics(
    current_user: UserType = Depends(get_current_user)
):
    """Принудительный сбор метрик производительности"""
    performance_collector.record_system_metrics()
    return {"message": "Performance metrics collected successfully"}


@router.post("/cleanup")
async def cleanup_old_metrics(
    current_user: UserType = Depends(get_current_user),
    hours: int = Query(24, description="Удалить метрики старше указанного количества часов")
):
    """Очистка старых метрик"""
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    older_than = timedelta(hours=hours)
    metrics_collector.clear_old_metrics(older_than)
    
    return {"message": f"Metrics older than {hours} hours cleared successfully"}


@router.get("/export/json")
async def export_metrics_json(
    current_user: UserType = Depends(get_current_user),
    metric_names: Optional[List[str]] = Query(None, description="Список метрик для экспорта"),
    since: Optional[datetime] = Query(None, description="Экспортировать данные с этого времени")
):
    """Экспорт метрик в JSON"""
    result = {}
    
    all_metrics = metrics_collector.get_all_metrics()
    metrics_to_export = metric_names or list(all_metrics.keys())
    
    for metric_name in metrics_to_export:
        if metric_name in all_metrics:
            values = metrics_collector.get_values(metric_name, since)
            result[metric_name] = {
                "definition": all_metrics[metric_name].get("definition"),
                "statistics": metrics_collector.get_statistics(metric_name, since),
                "values": [
                    {
                        "value": v.value,
                        "timestamp": v.timestamp.isoformat(),
                        "tags": v.tags,
                        "metadata": v.metadata
                    }
                    for v in values
                ]
            }
    
    return result


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: UserType = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение сводки для дашборда"""
    # Обновляем метрики
    await business_collector.collect_all_business_metrics(db)
    performance_collector.record_system_metrics()
    
    # Основные показатели
    summary = {
        "business": {
            "requests_total": metrics_collector.get_latest_value("requests_total"),
            "conversion_rate": metrics_collector.get_latest_value("conversion_rate"),
            "revenue_daily": metrics_collector.get_latest_value("revenue_daily"),
            "active_users": metrics_collector.get_latest_value("active_users"),
        },
        "performance": {
            "memory_usage": metrics_collector.get_latest_value("memory_usage"),
            "cpu_usage": metrics_collector.get_latest_value("cpu_usage"),
            "http_requests_total": metrics_collector.get_latest_value("http_requests_total"),
            "db_queries_total": metrics_collector.get_latest_value("db_queries_total"),
        },
        "system": {
            "cache_hit_rate": calculate_cache_hit_rate(),
            "error_rate": metrics_collector.get_latest_value("error_rate"),
            "uptime": get_system_uptime(),
        }
    }
    
    return summary


def calculate_cache_hit_rate() -> float:
    """Вычисление коэффициента попаданий в кэш"""
    hits = metrics_collector.get_latest_value("cache_hits") or 0
    misses = metrics_collector.get_latest_value("cache_misses") or 0
    
    if hits + misses == 0:
        return 0.0
    
    return (hits / (hits + misses)) * 100


def get_system_uptime() -> str:
    """Получение времени работы системы"""
    try:
        import psutil
        boot_time = psutil.boot_time()
        uptime = datetime.now().timestamp() - boot_time
        
        days = int(uptime // 86400)
        hours = int((uptime % 86400) // 3600)
        minutes = int((uptime % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except (OSError, ValueError) as e:
        logger.warning(f"Error getting system uptime: {e}")
        return "Unknown"


@router.get("/prometheus")
async def get_prometheus_metrics():
    """Получить метрики в формате Prometheus (публичный эндпоинт для Prometheus)"""
    from fastapi.responses import Response
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    ) 
