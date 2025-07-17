"""
API endpoints для управления безопасностью
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.auth import require_admin
from ..core.models import Administrator
from ..core.security import LoginAttemptTracker, login_attempts, csrf_tokens, get_client_ip

router = APIRouter(prefix="/security", tags=["security"])

@router.get("/login-attempts")
async def get_login_attempts_stats(
    current_user: Administrator = Depends(require_admin)
) -> Dict[str, Any]:
    """Получить статистику попыток входа"""
    try:
        stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "failed_attempts": 0,
            "locked_accounts": 0,
            "unique_ips": set(),
            "recent_attempts": []
        }
        
        current_time = datetime.utcnow()
        
        for attempt_key, data in login_attempts.items():
            ip_address, username = attempt_key.split(":", 1)
            stats["unique_ips"].add(ip_address)
            
            # Проверяем блокировку
            if data.get("locked_until") and current_time < data["locked_until"]:
                stats["locked_accounts"] += 1
            
            # Анализируем попытки
            for attempt in data.get("attempts", []):
                stats["total_attempts"] += 1
                if attempt["success"]:
                    stats["successful_attempts"] += 1
                else:
                    stats["failed_attempts"] += 1
                
                # Добавляем недавние попытки
                if len(stats["recent_attempts"]) < 20:
                    stats["recent_attempts"].append({
                        "username": username,
                        "ip_address": ip_address,
                        "success": attempt["success"],
                        "timestamp": attempt["timestamp"].isoformat(),
                        "user_agent": attempt.get("user_agent", "")
                    })
        
        stats["unique_ips"] = len(stats["unique_ips"])
        stats["success_rate"] = (
            stats["successful_attempts"] / stats["total_attempts"] * 100
            if stats["total_attempts"] > 0 else 0
        )
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get login attempts stats: {str(e)}"
        )

@router.get("/locked-accounts")
async def get_locked_accounts(
    current_user: Administrator = Depends(require_admin)
) -> List[Dict[str, Any]]:
    """Получить список заблокированных аккаунтов"""
    try:
        locked_accounts = []
        current_time = datetime.utcnow()
        
        for attempt_key, data in login_attempts.items():
            locked_until = data.get("locked_until")
            if locked_until and current_time < locked_until:
                ip_address, username = attempt_key.split(":", 1)
                remaining_time = int((locked_until - current_time).total_seconds())
                
                locked_accounts.append({
                    "username": username,
                    "ip_address": ip_address,
                    "locked_until": locked_until.isoformat(),
                    "remaining_seconds": remaining_time,
                    "total_attempts": data.get("total_attempts", 0),
                    "failed_attempts": len([
                        a for a in data.get("attempts", [])
                        if not a["success"]
                    ])
                })
        
        return locked_accounts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get locked accounts: {str(e)}"
        )

@router.post("/unlock-account")
async def unlock_account(
    username: str,
    ip_address: str,
    current_user: Administrator = Depends(require_admin)
) -> Dict[str, str]:
    """Разблокировать аккаунт"""
    try:
        attempt_key = f"{ip_address}:{username}"
        
        if attempt_key in login_attempts:
            login_attempts[attempt_key]["locked_until"] = None
            return {"message": f"Account {username} from {ip_address} has been unlocked"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found or not locked"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlock account: {str(e)}"
        )

@router.get("/csrf-tokens")
async def get_csrf_tokens_stats(
    current_user: Administrator = Depends(require_admin)
) -> Dict[str, Any]:
    """Получить статистику CSRF токенов"""
    try:
        current_time = datetime.utcnow()
        
        stats = {
            "total_tokens": len(csrf_tokens),
            "expired_tokens": 0,
            "valid_tokens": 0,
            "tokens_info": []
        }
        
        for session_id, token_data in csrf_tokens.items():
            is_expired = current_time > token_data["expires_at"]
            
            if is_expired:
                stats["expired_tokens"] += 1
            else:
                stats["valid_tokens"] += 1
            
            stats["tokens_info"].append({
                "session_id": session_id[:8] + "...",  # Маскируем для безопасности
                "created_at": token_data["created_at"].isoformat(),
                "expires_at": token_data["expires_at"].isoformat(),
                "is_expired": is_expired,
                "remaining_seconds": max(0, int((token_data["expires_at"] - current_time).total_seconds()))
            })
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CSRF tokens stats: {str(e)}"
        )

@router.post("/cleanup-expired")
async def cleanup_expired_data(
    current_user: Administrator = Depends(require_admin)
) -> Dict[str, Any]:
    """Очистить просроченные данные безопасности"""
    try:
        from ..core.security import cleanup_security_data
        
        # Подсчитываем данные до очистки
        before_csrf = len(csrf_tokens)
        before_attempts = len(login_attempts)
        
        # Выполняем очистку
        await cleanup_security_data()
        
        # Подсчитываем данные после очистки
        after_csrf = len(csrf_tokens)
        after_attempts = len(login_attempts)
        
        return {
            "message": "Expired security data cleaned up",
            "csrf_tokens_removed": before_csrf - after_csrf,
            "login_attempts_removed": before_attempts - after_attempts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired data: {str(e)}"
        )

@router.get("/security-summary")
async def get_security_summary(
    current_user: Administrator = Depends(require_admin)
) -> Dict[str, Any]:
    """Получить сводку по безопасности"""
    try:
        current_time = datetime.utcnow()
        
        # Статистика попыток входа
        total_attempts = sum(len(data.get("attempts", [])) for data in login_attempts.values())
        failed_attempts = sum(
            len([a for a in data.get("attempts", []) if not a["success"]])
            for data in login_attempts.values()
        )
        locked_accounts = sum(
            1 for data in login_attempts.values()
            if data.get("locked_until") and current_time < data["locked_until"]
        )
        
        # Статистика CSRF
        valid_csrf_tokens = sum(
            1 for token_data in csrf_tokens.values()
            if current_time <= token_data["expires_at"]
        )
        
        # Недавние события безопасности
        recent_events = []
        for attempt_key, data in login_attempts.items():
            ip_address, username = attempt_key.split(":", 1)
            for attempt in data.get("attempts", [])[-5:]:  # Последние 5 попыток
                recent_events.append({
                    "type": "login_attempt",
                    "username": username,
                    "ip_address": ip_address,
                    "success": attempt["success"],
                    "timestamp": attempt["timestamp"].isoformat()
                })
        
        # Сортируем по времени
        recent_events.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_events = recent_events[:20]  # Топ 20 событий
        
        return {
            "login_attempts": {
                "total": total_attempts,
                "failed": failed_attempts,
                "success_rate": ((total_attempts - failed_attempts) / total_attempts * 100) if total_attempts > 0 else 0
            },
            "account_security": {
                "locked_accounts": locked_accounts,
                "unique_ips": len(set(key.split(":", 1)[0] for key in login_attempts.keys()))
            },
            "csrf_protection": {
                "active_tokens": valid_csrf_tokens,
                "total_sessions": len(csrf_tokens)
            },
            "recent_events": recent_events,
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security summary: {str(e)}"
        ) 