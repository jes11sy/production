"""
Публичные эндпоинты для Prometheus метрик
"""
from fastapi import APIRouter
from fastapi.responses import Response
from ..monitoring.prometheus_metrics import get_metrics, get_metrics_content_type

router = APIRouter(prefix="/metrics", tags=["prometheus-metrics"])


@router.get("/prometheus")
async def get_prometheus_metrics():
    """Получить метрики в формате Prometheus (публичный эндпоинт)"""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    ) 