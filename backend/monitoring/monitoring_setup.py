#!/usr/bin/env python3
"""
Единый скрипт для настройки мониторинга и визуализации
Интеграция с Prometheus, Grafana и система алертинга
"""
import asyncio
import logging
import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    """Настройка системы мониторинга"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dashboards_dir = self.project_root / "grafana_dashboards"
        self.config_dir = self.project_root / "monitoring_config"
        
    def create_directories(self):
        """Создать необходимые директории"""
        directories = [
            self.dashboards_dir,
            self.config_dir,
            self.project_root / "logs",
            self.project_root / "data"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def install_dependencies(self):
        """Установить зависимости для мониторинга"""
        dependencies = [
            "prometheus-client",
            "aiohttp",
            "psutil",
            "requests"
        ]
        
        logger.info("Installing monitoring dependencies...")
        
        for dep in dependencies:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True, capture_output=True)
                logger.info(f"Installed: {dep}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {dep}: {e}")
    
    def generate_prometheus_config(self):
        """Создать конфигурацию Prometheus"""
        config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [
                "alerting_rules.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["localhost:9093"]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": [
                {
                    "job_name": "requests-system",
                    "static_configs": [
                        {
                            "targets": ["localhost:8001"]
                        }
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s"
                }
            ]
        }
        
        config_file = self.config_dir / "prometheus.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Prometheus config created: {config_file}")
    
    def generate_alerting_rules(self):
        """Создать правила алертинга для Prometheus"""
        rules = {
            "groups": [
                {
                    "name": "system_alerts",
                    "rules": [
                        {
                            "alert": "HighCPUUsage",
                            "expr": "cpu_usage_percent > 80",
                            "for": "5m",
                            "labels": {
                                "severity": "warning",
                                "component": "system"
                            },
                            "annotations": {
                                "summary": "High CPU usage",
                                "description": "CPU usage is above 80% for 5 minutes"
                            }
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "memory_usage_bytes / 1024 / 1024 / 1024 > 8",
                            "for": "5m",
                            "labels": {
                                "severity": "critical",
                                "component": "system"
                            },
                            "annotations": {
                                "summary": "High memory usage",
                                "description": "Memory usage is above 8GB"
                            }
                        },
                        {
                            "alert": "HighErrorRate",
                            "expr": "rate(errors_total[5m]) > 0.1",
                            "for": "2m",
                            "labels": {
                                "severity": "critical",
                                "component": "errors"
                            },
                            "annotations": {
                                "summary": "High error rate",
                                "description": "Error rate is above threshold"
                            }
                        },
                        {
                            "alert": "HighResponseTime",
                            "expr": "histogram_quantile(0.95, rate(response_time_seconds_bucket[5m])) > 2",
                            "for": "5m",
                            "labels": {
                                "severity": "warning",
                                "component": "performance"
                            },
                            "annotations": {
                                "summary": "High response time",
                                "description": "Response time is above 2 seconds"
                            }
                        },
                        {
                            "alert": "HighDatabaseConnections",
                            "expr": "database_connections > 20",
                            "for": "5m",
                            "labels": {
                                "severity": "warning",
                                "component": "database"
                            },
                            "annotations": {
                                "summary": "High database connections",
                                "description": "Too many database connections"
                            }
                        },
                        {
                            "alert": "SecurityViolations",
                            "expr": "rate(security_violations_total[5m]) > 0",
                            "for": "1m",
                            "labels": {
                                "severity": "critical",
                                "component": "security"
                            },
                            "annotations": {
                                "summary": "Security violations",
                                "description": "Security violations detected"
                            }
                        }
                    ]
                }
            ]
        }
        
        rules_file = self.config_dir / "alerting_rules.yml"
        with open(rules_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(rules, f, default_flow_style=False)
        
        logger.info(f"Alerting rules created: {rules_file}")
    
    def generate_grafana_datasource_config(self):
        """Создать конфигурацию источника данных Grafana"""
        datasource_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "url": "http://localhost:9090",
                    "access": "proxy",
                    "isDefault": True,
                    "jsonData": {
                        "timeInterval": "15s"
                    }
                }
            ]
        }
        
        config_file = self.config_dir / "grafana_datasources.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(datasource_config, f, default_flow_style=False)
        
        logger.info(f"Grafana datasource config created: {config_file}")
    
    def create_docker_compose(self):
        """Создать docker-compose.yml для мониторинга"""
        compose_config = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "prometheus",
                    "ports": ["9090:9090"],
                    "volumes": [
                        f"{self.config_dir}/prometheus.yml:/etc/prometheus/prometheus.yml",
                        f"{self.config_dir}/alerting_rules.yml:/etc/prometheus/alerting_rules.yml",
                        "prometheus_data:/prometheus"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ],
                    "restart": "unless-stopped"
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "grafana",
                    "ports": ["3000:3000"],
                    "environment": {
                        "GF_SECURITY_ADMIN_PASSWORD": "admin",
                        "GF_USERS_ALLOW_SIGN_UP": "false"
                    },
                    "volumes": [
                        f"{self.config_dir}/grafana_datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml",
                        "grafana_data:/var/lib/grafana"
                    ],
                    "restart": "unless-stopped"
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "container_name": "alertmanager",
                    "ports": ["9093:9093"],
                    "volumes": [
                        f"{self.config_dir}/alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                    ],
                    "command": [
                        "--config.file=/etc/alertmanager/alertmanager.yml",
                        "--storage.path=/alertmanager"
                    ],
                    "restart": "unless-stopped"
                }
            },
            "volumes": {
                "prometheus_data": {},
                "grafana_data": {}
            }
        }
        
        compose_file = self.project_root / "docker-compose.monitoring.yml"
        with open(compose_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(compose_config, f, default_flow_style=False)
        
        logger.info(f"Docker Compose file created: {compose_file}")
    
    def create_alertmanager_config(self):
        """Создать конфигурацию Alertmanager"""
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@yourcompany.com"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [
                {
                    "name": "web.hook",
                    "webhook_configs": [
                        {
                            "url": "http://localhost:5001/api/alerts"
                        }
                    ]
                }
            ]
        }
        
        config_file = self.config_dir / "alertmanager.yml"
        with open(config_file, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Alertmanager config created: {config_file}")
    
    def create_startup_script(self):
        """Создать скрипт запуска мониторинга"""
        script_content = """#!/bin/bash
# Скрипт запуска системы мониторинга

echo "🚀 Запуск системы мониторинга..."

# Запуск Prometheus интеграции
echo "📊 Запуск Prometheus интеграции..."
python prometheus_integration.py &
PROMETHEUS_PID=$!

# Запуск системы алертинга
echo "🚨 Запуск системы алертинга..."
python alerting_config.py &
ALERTING_PID=$!

# Запуск Docker контейнеров
echo "🐳 Запуск Docker контейнеров..."
docker-compose -f docker-compose.monitoring.yml up -d

echo "✅ Система мониторинга запущена!"
echo ""
echo "📊 Доступные сервисы:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Метрики: http://localhost:8001/metrics"
echo ""
echo "🛑 Для остановки:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
echo "  kill $PROMETHEUS_PID $ALERTING_PID"

# Ожидание сигнала для корректного завершения
trap 'echo "Остановка мониторинга..."; docker-compose -f docker-compose.monitoring.yml down; kill $PROMETHEUS_PID $ALERTING_PID; exit' INT TERM
wait
"""
        
        script_file = self.project_root / "start_monitoring.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Делаем скрипт исполняемым
        os.chmod(script_file, 0o755)
        
        logger.info(f"Startup script created: {script_file}")
    
    def create_windows_batch_script(self):
        """Создать batch скрипт для Windows"""
        script_content = """@echo off
REM Скрипт запуска системы мониторинга для Windows

echo 🚀 Запуск системы мониторинга...

REM Запуск Prometheus интеграции
echo 📊 Запуск Prometheus интеграции...
start /B python prometheus_integration.py

REM Запуск системы алертинга
echo 🚨 Запуск системы алертинга...
start /B python alerting_config.py

REM Запуск Docker контейнеров
echo 🐳 Запуск Docker контейнеров...
docker-compose -f docker-compose.monitoring.yml up -d

echo ✅ Система мониторинга запущена!
echo.
echo 📊 Доступные сервисы:
echo   - Prometheus: http://localhost:9090
echo   - Grafana: http://localhost:3000 (admin/admin)
echo   - Alertmanager: http://localhost:9093
echo   - Метрики: http://localhost:8001/metrics
echo.
echo 🛑 Для остановки:
echo   docker-compose -f docker-compose.monitoring.yml down
echo   taskkill /F /IM python.exe
echo.
pause
"""
        
        script_file = self.project_root / "start_monitoring.bat"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Windows batch script created: {script_file}")
    
    def create_readme(self):
        """Создать README для мониторинга"""
        readme_content = """# 📊 Система мониторинга и визуализации

## 🚀 Быстрый запуск

### Linux/Mac:
```bash
chmod +x start_monitoring.sh
./start_monitoring.sh
```

### Windows:
```cmd
start_monitoring.bat
```

## 📋 Компоненты системы

### 1. Prometheus
- **URL**: http://localhost:9090
- **Назначение**: Сбор и хранение метрик
- **Конфигурация**: `monitoring_config/prometheus.yml`

### 2. Grafana
- **URL**: http://localhost:3000
- **Логин**: admin/admin
- **Назначение**: Визуализация метрик
- **Дашборды**: `grafana_dashboards/`

### 3. Alertmanager
- **URL**: http://localhost:9093
- **Назначение**: Управление алертами
- **Конфигурация**: `monitoring_config/alertmanager.yml`

### 4. Метрики приложения
- **URL**: http://localhost:8001/metrics
- **Назначение**: Экспорт метрик приложения

## 📊 Доступные дашборды

1. **System Overview** - Общий обзор системы
   - CPU и Memory usage
   - HTTP requests
   - Database connections
   - Response times

2. **Business Metrics** - Бизнес-метрики
   - Total requests
   - Transactions
   - Active users
   - Request rates

3. **Security Dashboard** - Безопасность
   - Login attempts
   - Security violations
   - Error rates

4. **Performance Dashboard** - Производительность
   - Cache hit rate
   - Database query duration
   - HTTP request duration

## 🚨 Алерты

### Системные алерты:
- High CPU usage (>80%)
- High memory usage (>8GB)
- High error rate (>0.1 errors/s)

### Производительность:
- High response time (>2s)
- High database connections (>20)
- Slow database queries (>1s)

### Безопасность:
- High login failures (>10/min)
- Security violations

### Бизнес:
- Low request rate (<1 req/s)
- No active users

## ⚙️ Конфигурация

### Настройка уведомлений:
1. Отредактируйте `alerting_config.py`
2. Настройте email/Slack/webhook каналы
3. Перезапустите систему алертинга

### Добавление новых метрик:
1. Добавьте метрики в `prometheus_integration.py`
2. Создайте новые панели в Grafana
3. Добавьте правила алертов при необходимости

## 🛠️ Устранение неполадок

### Prometheus недоступен:
```bash
docker logs prometheus
```

### Grafana недоступен:
```bash
docker logs grafana
```

### Метрики не собираются:
```bash
curl http://localhost:8001/metrics
```

## 📈 Расширение системы

### Добавление новых источников данных:
1. Добавьте новый scrape_config в prometheus.yml
2. Создайте соответствующие дашборды в Grafana

### Настройка retention:
- Prometheus: 200h (по умолчанию)
- Grafana: бессрочно
- Alertmanager: 120h

## 🔧 Ручная настройка

### Установка зависимостей:
```bash
pip install prometheus-client aiohttp psutil requests pyyaml
```

### Запуск компонентов по отдельности:
```bash
# Prometheus интеграция
python prometheus_integration.py

# Система алертинга
python alerting_config.py

# Docker контейнеры
docker-compose -f docker-compose.monitoring.yml up -d
```

## 📝 Логи

- Prometheus: `docker logs prometheus`
- Grafana: `docker logs grafana`
- Alertmanager: `docker logs alertmanager`
- Приложение: `logs/monitoring.log`
"""
        
        readme_file = self.project_root / "MONITORING_README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info(f"Monitoring README created: {readme_file}")
    
    def setup_monitoring(self):
        """Полная настройка системы мониторинга"""
        logger.info("🔧 Настройка системы мониторинга...")
        
        try:
            # Создаем директории
            self.create_directories()
            
            # Устанавливаем зависимости
            self.install_dependencies()
            
            # Генерируем конфигурации
            self.generate_prometheus_config()
            self.generate_alerting_rules()
            self.generate_grafana_datasource_config()
            self.create_alertmanager_config()
            
            # Создаем Docker Compose
            self.create_docker_compose()
            
            # Создаем скрипты запуска
            self.create_startup_script()
            self.create_windows_batch_script()
            
            # Создаем документацию
            self.create_readme()
            
            logger.info("✅ Система мониторинга настроена успешно!")
            
            print("\n🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
            print("\n📊 Доступные сервисы:")
            print("  - Prometheus: http://localhost:9090")
            print("  - Grafana: http://localhost:3000 (admin/admin)")
            print("  - Alertmanager: http://localhost:9093")
            print("  - Метрики: http://localhost:8001/metrics")
            
            print("\n🚀 Для запуска:")
            print("  Linux/Mac: ./start_monitoring.sh")
            print("  Windows: start_monitoring.bat")
            
        except Exception as e:
            logger.error(f"❌ Ошибка настройки: {e}")
            raise


def main():
    """Основная функция"""
    setup = MonitoringSetup()
    setup.setup_monitoring()


if __name__ == "__main__":
    main() 