#!/usr/bin/env python3
"""
Конфигурация системы алертинга для мониторинга
Настройка правил алертов и уведомлений
"""
import asyncio
import logging
import json
import smtplib
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """Правило алерта"""
    name: str
    condition: str
    severity: str  # critical, warning, info
    duration: str  # 5m, 10m, 1h
    description: str
    labels: Dict[str, str]
    annotations: Dict[str, str]

@dataclass
class NotificationChannel:
    """Канал уведомлений"""
    name: str
    type: str  # email, slack, webhook
    config: Dict[str, Any]

class AlertingSystem:
    """Система алертинга"""
    
    def __init__(self):
        self.alert_rules = []
        self.notification_channels = []
        self.active_alerts = {}
        
    def add_alert_rule(self, rule: AlertRule):
        """Добавить правило алерта"""
        self.alert_rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def add_notification_channel(self, channel: NotificationChannel):
        """Добавить канал уведомлений"""
        self.notification_channels.append(channel)
        logger.info(f"Added notification channel: {channel.name}")
    
    def create_default_alert_rules(self):
        """Создать стандартные правила алертов"""
        
        # Системные алерты
        self.add_alert_rule(AlertRule(
            name="HighCPUUsage",
            condition="cpu_usage_percent > 80",
            severity="warning",
            duration="5m",
            description="CPU usage is above 80% for 5 minutes",
            labels={"severity": "warning", "component": "system"},
            annotations={"summary": "High CPU usage", "description": "CPU usage is above 80%"}
        ))
        
        self.add_alert_rule(AlertRule(
            name="HighMemoryUsage",
            condition="memory_usage_bytes / 1024 / 1024 / 1024 > 8",
            severity="critical",
            duration="5m",
            description="Memory usage is above 8GB for 5 minutes",
            labels={"severity": "critical", "component": "system"},
            annotations={"summary": "High memory usage", "description": "Memory usage is above 8GB"}
        ))
        
        # Производительность
        self.add_alert_rule(AlertRule(
            name="HighResponseTime",
            condition="histogram_quantile(0.95, rate(response_time_seconds_bucket[5m])) > 2",
            severity="warning",
            duration="5m",
            description="95th percentile response time is above 2 seconds",
            labels={"severity": "warning", "component": "performance"},
            annotations={"summary": "High response time", "description": "Response time is above 2 seconds"}
        ))
        
        self.add_alert_rule(AlertRule(
            name="HighErrorRate",
            condition="rate(errors_total[5m]) > 0.1",
            severity="critical",
            duration="2m",
            description="Error rate is above 0.1 errors per second",
            labels={"severity": "critical", "component": "errors"},
            annotations={"summary": "High error rate", "description": "Error rate is above threshold"}
        ))
        
        # База данных
        self.add_alert_rule(AlertRule(
            name="HighDatabaseConnections",
            condition="database_connections > 20",
            severity="warning",
            duration="5m",
            description="Database connection count is above 20",
            labels={"severity": "warning", "component": "database"},
            annotations={"summary": "High database connections", "description": "Too many database connections"}
        ))
        
        self.add_alert_rule(AlertRule(
            name="SlowDatabaseQueries",
            condition="histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m])) > 1",
            severity="warning",
            duration="5m",
            description="Database queries are taking longer than 1 second",
            labels={"severity": "warning", "component": "database"},
            annotations={"summary": "Slow database queries", "description": "Database queries are slow"}
        ))
        
        # Безопасность
        self.add_alert_rule(AlertRule(
            name="HighLoginFailures",
            condition="rate(login_attempts_total{status=\"failed\"}[5m]) > 10",
            severity="critical",
            duration="2m",
            description="High rate of failed login attempts",
            labels={"severity": "critical", "component": "security"},
            annotations={"summary": "High login failures", "description": "Possible brute force attack"}
        ))
        
        self.add_alert_rule(AlertRule(
            name="SecurityViolations",
            condition="rate(security_violations_total[5m]) > 0",
            severity="critical",
            duration="1m",
            description="Security violations detected",
            labels={"severity": "critical", "component": "security"},
            annotations={"summary": "Security violations", "description": "Security violations detected"}
        ))
        
        # Бизнес метрики
        self.add_alert_rule(AlertRule(
            name="LowRequestRate",
            condition="rate(requests_total[5m]) < 1",
            severity="warning",
            duration="10m",
            description="Request rate is below 1 request per second",
            labels={"severity": "warning", "component": "business"},
            annotations={"summary": "Low request rate", "description": "System may be underutilized"}
        ))
        
        self.add_alert_rule(AlertRule(
            name="NoActiveUsers",
            condition="active_users < 1",
            severity="warning",
            duration="15m",
            description="No active users for 15 minutes",
            labels={"severity": "warning", "component": "business"},
            annotations={"summary": "No active users", "description": "No users are currently active"}
        ))
        
        # Кеш
        self.add_alert_rule(AlertRule(
            name="LowCacheHitRate",
            condition="rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) < 0.8",
            severity="warning",
            duration="10m",
            description="Cache hit rate is below 80%",
            labels={"severity": "warning", "component": "cache"},
            annotations={"summary": "Low cache hit rate", "description": "Cache performance is poor"}
        ))
        
        logger.info(f"Created {len(self.alert_rules)} default alert rules")
    
    def create_default_notification_channels(self):
        """Создать стандартные каналы уведомлений"""
        
        # Email канал
        email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "alerts@yourcompany.com",
            "password": "your_password",
            "from_email": "alerts@yourcompany.com",
            "to_emails": ["admin@yourcompany.com", "devops@yourcompany.com"]
        }
        
        self.add_notification_channel(NotificationChannel(
            name="EmailAlerts",
            type="email",
            config=email_config
        ))
        
        # Slack канал
        slack_config = {
            "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "channel": "#alerts",
            "username": "Alerting Bot"
        }
        
        self.add_notification_channel(NotificationChannel(
            name="SlackAlerts",
            type="slack",
            config=slack_config
        ))
        
        # Webhook канал
        webhook_config = {
            "url": "https://your-webhook-endpoint.com/alerts",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer your-token"
            }
        }
        
        self.add_notification_channel(NotificationChannel(
            name="WebhookAlerts",
            type="webhook",
            config=webhook_config
        ))
        
        logger.info(f"Created {len(self.notification_channels)} notification channels")
    
    async def send_email_alert(self, channel: NotificationChannel, alert_data: Dict[str, Any]):
        """Отправить email алерт"""
        try:
            config = channel.config
            
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"ALERT: {alert_data['name']}"
            
            body = f"""
            Alert: {alert_data['name']}
            Severity: {alert_data['severity']}
            Description: {alert_data['description']}
            Time: {alert_data['timestamp']}
            
            Condition: {alert_data['condition']}
            Duration: {alert_data['duration']}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email alert sent: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def send_slack_alert(self, channel: NotificationChannel, alert_data: Dict[str, Any]):
        """Отправить Slack алерт"""
        try:
            config = channel.config
            
            payload = {
                "channel": config['channel'],
                "username": config['username'],
                "text": f"🚨 *ALERT: {alert_data['name']}*\n"
                       f"Severity: {alert_data['severity']}\n"
                       f"Description: {alert_data['description']}\n"
                       f"Time: {alert_data['timestamp']}",
                "icon_emoji": ":warning:"
            }
            
            response = requests.post(config['webhook_url'], json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack alert sent: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def send_webhook_alert(self, channel: NotificationChannel, alert_data: Dict[str, Any]):
        """Отправить webhook алерт"""
        try:
            config = channel.config
            
            payload = {
                "alert": alert_data['name'],
                "severity": alert_data['severity'],
                "description": alert_data['description'],
                "timestamp": alert_data['timestamp'],
                "condition": alert_data['condition'],
                "duration": alert_data['duration']
            }
            
            response = requests.post(
                config['url'],
                json=payload,
                headers=config['headers']
            )
            response.raise_for_status()
            
            logger.info(f"Webhook alert sent: {alert_data['name']}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def send_notification(self, alert_data: Dict[str, Any]):
        """Отправить уведомление по всем каналам"""
        for channel in self.notification_channels:
            try:
                if channel.type == "email":
                    await self.send_email_alert(channel, alert_data)
                elif channel.type == "slack":
                    await self.send_slack_alert(channel, alert_data)
                elif channel.type == "webhook":
                    await self.send_webhook_alert(channel, alert_data)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.type}: {e}")
    
    def check_alert_condition(self, rule: AlertRule, metrics_data: Dict[str, float]) -> bool:
        """Проверить условие алерта"""
        try:
            # Простая проверка условий (в реальной системе нужна более сложная логика)
            if rule.condition == "cpu_usage_percent > 80":
                return metrics_data.get('cpu_usage_percent', 0) > 80
            elif rule.condition == "memory_usage_bytes / 1024 / 1024 / 1024 > 8":
                return (metrics_data.get('memory_usage_bytes', 0) / 1024 / 1024 / 1024) > 8
            elif rule.condition == "database_connections > 20":
                return metrics_data.get('database_connections', 0) > 20
            elif rule.condition == "redis_connections > 10":
                return metrics_data.get('redis_connections', 0) > 10
            else:
                # Для других условий возвращаем False (нужна более сложная логика)
                return False
        except Exception as e:
            logger.error(f"Error checking alert condition: {e}")
            return False
    
    async def evaluate_alerts(self, metrics_data: Dict[str, float]):
        """Оценить все алерты"""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            alert_key = f"{rule.name}_{rule.severity}"
            
            # Проверяем условие алерта
            if self.check_alert_condition(rule, metrics_data):
                # Алерт активен
                if alert_key not in self.active_alerts:
                    # Новый алерт
                    self.active_alerts[alert_key] = {
                        "rule": rule,
                        "start_time": current_time,
                        "last_check": current_time
                    }
                    
                    # Отправляем уведомление
                    alert_data = {
                        "name": rule.name,
                        "severity": rule.severity,
                        "description": rule.description,
                        "timestamp": current_time.isoformat(),
                        "condition": rule.condition,
                        "duration": rule.duration
                    }
                    
                    await self.send_notification(alert_data)
                    logger.warning(f"New alert triggered: {rule.name}")
                
                else:
                    # Обновляем существующий алерт
                    self.active_alerts[alert_key]["last_check"] = current_time
            else:
                # Алерт неактивен
                if alert_key in self.active_alerts:
                    # Алерт разрешен
                    del self.active_alerts[alert_key]
                    logger.info(f"Alert resolved: {rule.name}")
    
    def save_configuration(self, filename: str = "alerting_config.json"):
        """Сохранить конфигурацию алертинга"""
        config = {
            "alert_rules": [
                {
                    "name": rule.name,
                    "condition": rule.condition,
                    "severity": rule.severity,
                    "duration": rule.duration,
                    "description": rule.description,
                    "labels": rule.labels,
                    "annotations": rule.annotations
                }
                for rule in self.alert_rules
            ],
            "notification_channels": [
                {
                    "name": channel.name,
                    "type": channel.type,
                    "config": channel.config
                }
                for channel in self.notification_channels
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Alerting configuration saved to {filename}")
    
    def load_configuration(self, filename: str = "alerting_config.json"):
        """Загрузить конфигурацию алертинга"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Загружаем правила алертов
            self.alert_rules = []
            for rule_data in config.get("alert_rules", []):
                rule = AlertRule(
                    name=rule_data["name"],
                    condition=rule_data["condition"],
                    severity=rule_data["severity"],
                    duration=rule_data["duration"],
                    description=rule_data["description"],
                    labels=rule_data["labels"],
                    annotations=rule_data["annotations"]
                )
                self.alert_rules.append(rule)
            
            # Загружаем каналы уведомлений
            self.notification_channels = []
            for channel_data in config.get("notification_channels", []):
                channel = NotificationChannel(
                    name=channel_data["name"],
                    type=channel_data["type"],
                    config=channel_data["config"]
                )
                self.notification_channels.append(channel)
            
            logger.info(f"Alerting configuration loaded from {filename}")
            
        except FileNotFoundError:
            logger.warning(f"Configuration file {filename} not found, using defaults")
            self.create_default_alert_rules()
            self.create_default_notification_channels()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")


async def main():
    """Основная функция"""
    logger.info("Starting alerting system...")
    
    try:
        # Создаем систему алертинга
        alerting_system = AlertingSystem()
        
        # Загружаем или создаем конфигурацию
        alerting_system.load_configuration()
        
        # Сохраняем конфигурацию
        alerting_system.save_configuration()
        
        # Моковые метрики для тестирования
        test_metrics = {
            "cpu_usage_percent": 85.0,
            "memory_usage_bytes": 9.0 * 1024 * 1024 * 1024,  # 9GB
            "database_connections": 25.0,
            "redis_connections": 15.0
        }
        
        # Оцениваем алерты
        await alerting_system.evaluate_alerts(test_metrics)
        
        logger.info("Alerting system started successfully!")
        
    except Exception as e:
        logger.error(f"Error in alerting system: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 