"""
API эндпоинты для расширенного мониторинга системы
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from app.core.auth import get_current_user
from app.monitoring.connection_pool_monitor import pool_monitor
from app.monitoring.redis_monitor import redis_monitor
from app.monitoring.alerts import alert_manager, AlertSeverity, create_custom_alert
from app.monitoring.metrics import metrics_collector

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/pool/status")
async def get_pool_status(current_user: dict = Depends(get_current_user)):
    """Получение статуса пула соединений"""
    try:
        # Проверяем кешированные данные
        cached_data = await pool_monitor.get_cached_metrics()
        if cached_data:
            return JSONResponse(content=cached_data)
        
        # Получаем свежие данные
        health_info = await pool_monitor.check_pool_health()
        return JSONResponse(content=health_info)
        
    except Exception as e:
        logger.error(f"Error getting pool status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pool status")


@router.get("/pool/metrics")
async def get_pool_metrics(current_user: dict = Depends(get_current_user)):
    """Получение метрик пула соединений"""
    try:
        metrics = pool_monitor.get_pool_metrics()
        return JSONResponse(content=metrics.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting pool metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pool metrics")


@router.get("/pool/statistics")
async def get_pool_statistics(current_user: dict = Depends(get_current_user)):
    """Получение статистики пула соединений"""
    try:
        stats = pool_monitor.get_pool_statistics()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting pool statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pool statistics")


@router.get("/pool/slow-queries")
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Получение медленных запросов"""
    try:
        slow_queries = list(pool_monitor.slow_queries)[-limit:]
        return JSONResponse(content=[q.to_dict() for q in slow_queries])
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get slow queries")


@router.get("/redis/status")
async def get_redis_status(current_user: dict = Depends(get_current_user)):
    """Получение статуса Redis"""
    try:
        # Проверяем кешированные данные
        cached_data = await redis_monitor.get_cached_metrics()
        if cached_data:
            return JSONResponse(content=cached_data)
        
        # Получаем свежие данные
        health_info = await redis_monitor.check_redis_health()
        return JSONResponse(content=health_info)
        
    except Exception as e:
        logger.error(f"Error getting Redis status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis status")


@router.get("/redis/metrics")
async def get_redis_metrics(current_user: dict = Depends(get_current_user)):
    """Получение метрик Redis"""
    try:
        metrics = await redis_monitor.get_redis_metrics()
        return JSONResponse(content=metrics.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting Redis metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis metrics")


@router.get("/redis/info")
async def get_redis_info(current_user: dict = Depends(get_current_user)):
    """Получение подробной информации о Redis"""
    try:
        info = await redis_monitor.get_redis_info()
        return JSONResponse(content=info)
        
    except Exception as e:
        logger.error(f"Error getting Redis info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis info")


@router.get("/redis/slow-log")
async def get_redis_slow_log(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Получение медленных команд Redis"""
    try:
        slow_log = await redis_monitor.get_slow_log()
        return JSONResponse(content=[cmd.to_dict() for cmd in slow_log[-limit:]])
        
    except Exception as e:
        logger.error(f"Error getting Redis slow log: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis slow log")


@router.get("/alerts/active")
async def get_active_alerts(current_user: dict = Depends(get_current_user)):
    """Получение активных алертов"""
    try:
        alerts = alert_manager.get_active_alerts()
        return JSONResponse(content=[alert.to_dict() for alert in alerts])
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")


@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None, regex="^(info|warning|critical|emergency)$"),
    current_user: dict = Depends(get_current_user)
):
    """Получение истории алертов"""
    try:
        alerts = alert_manager.get_alert_history(limit)
        
        # Фильтруем по серьезности если указано
        if severity:
            alerts = [alert for alert in alerts if alert.severity.value == severity]
        
        return JSONResponse(content=[alert.to_dict() for alert in alerts])
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert history")


@router.get("/alerts/statistics")
async def get_alert_statistics(current_user: dict = Depends(get_current_user)):
    """Получение статистики алертов"""
    try:
        stats = alert_manager.get_alert_statistics()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert statistics")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Подтверждение алерта"""
    try:
        success = alert_manager.acknowledge_alert(alert_id)
        if success:
            return JSONResponse(content={"status": "acknowledged", "alert_id": alert_id})
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.post("/alerts/{alert_id}/silence")
async def silence_alert(
    alert_id: str,
    duration_minutes: int = Query(60, ge=1, le=1440),
    current_user: dict = Depends(get_current_user)
):
    """Заглушение алерта"""
    try:
        success = alert_manager.silence_alert(alert_id, duration_minutes)
        if success:
            return JSONResponse(content={
                "status": "silenced", 
                "alert_id": alert_id,
                "duration_minutes": duration_minutes
            })
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
            
    except Exception as e:
        logger.error(f"Error silencing alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to silence alert")


@router.post("/alerts/custom")
async def create_custom_alert_endpoint(
    title: str,
    message: str,
    severity: str = Query("info", regex="^(info|warning|critical|emergency)$"),
    current_user: dict = Depends(get_current_user)
):
    """Создание кастомного алерта"""
    try:
        severity_enum = AlertSeverity(severity)
        alert = create_custom_alert(
            title=title,
            message=message,
            severity=severity_enum,
            tags={"created_by": current_user.get("login", "unknown")}
        )
        
        return JSONResponse(content=alert.to_dict())
        
    except Exception as e:
        logger.error(f"Error creating custom alert: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom alert")


@router.get("/system/health")
async def get_system_health(current_user: dict = Depends(get_current_user)):
    """Получение общего здоровья системы"""
    try:
        health_summary = await alert_manager.get_system_health_summary()
        return JSONResponse(content=health_summary)
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system health")


@router.get("/metrics/all")
async def get_all_metrics(current_user: dict = Depends(get_current_user)):
    """Получение всех метрик системы"""
    try:
        all_metrics = metrics_collector.get_all_metrics()
        return JSONResponse(content=all_metrics)
        
    except Exception as e:
        logger.error(f"Error getting all metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get all metrics")


@router.get("/metrics/{metric_name}")
async def get_metric(
    metric_name: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user)
):
    """Получение конкретной метрики"""
    try:
        values = metrics_collector.get_values(metric_name, limit=limit)
        statistics = metrics_collector.get_statistics(metric_name)
        
        return JSONResponse(content={
            "metric_name": metric_name,
            "values": [
                {
                    "value": v.value,
                    "timestamp": v.timestamp.isoformat(),
                    "tags": v.tags,
                    "metadata": v.metadata
                }
                for v in values
            ],
            "statistics": statistics
        })
        
    except Exception as e:
        logger.error(f"Error getting metric {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric {metric_name}")


@router.get("/dashboard/overview")
async def get_dashboard_overview(current_user: dict = Depends(get_current_user)):
    """Получение обзора для дашборда"""
    try:
        # Собираем ключевые метрики
        pool_metrics = pool_monitor.get_pool_metrics()
        redis_metrics = await redis_monitor.get_redis_metrics()
        active_alerts = alert_manager.get_active_alerts()
        system_health = await alert_manager.get_system_health_summary()
        
        # Ключевые показатели
        key_metrics = {
            "database": {
                "pool_utilization": pool_metrics.utilization_percent,
                "available_connections": pool_metrics.available_connections,
                "status": pool_metrics.status.value
            },
            "redis": {
                "connected": redis_metrics.connected,
                "memory_usage": redis_metrics.memory_usage_percent,
                "hit_rate": redis_metrics.hit_rate_percent,
                "status": redis_metrics.status.value
            },
            "system": {
                "active_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a.severity.value == "critical"]),
                "overall_status": system_health["system_status"]
            }
        }
        
        return JSONResponse(content={
            "timestamp": datetime.now().isoformat(),
            "key_metrics": key_metrics,
            "recent_alerts": [alert.to_dict() for alert in active_alerts[-5:]],
            "system_health": system_health
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard overview") 