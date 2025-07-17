#!/usr/bin/env python3
"""
Конфигурация Grafana dashboards для системы управления заявками
Создает JSON конфигурации для различных дашбордов
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List

class GrafanaDashboardGenerator:
    """Генератор дашбордов Grafana"""
    
    def __init__(self):
        self.base_config = {
            "dashboard": {
                "id": None,
                "title": "",
                "tags": [],
                "timezone": "browser",
                "panels": [],
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "refresh": "30s",
                "schemaVersion": 16,
                "version": 1,
                "links": [],
                "templating": {
                    "list": []
                }
            }
        }
    
    def create_system_overview_dashboard(self) -> Dict[str, Any]:
        """Создать дашборд общего обзора системы"""
        dashboard = self.base_config.copy()
        dashboard["dashboard"].update({
            "id": 1,
            "title": "System Overview",
            "tags": ["system", "overview"],
            "panels": [
                # CPU Usage
                {
                    "id": 1,
                    "title": "CPU Usage",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "cpu_usage_percent",
                            "legendFormat": "CPU %"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                },
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "red", "value": 80}
                                    ]
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 80}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                # Memory Usage
                {
                    "id": 2,
                    "title": "Memory Usage",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "memory_usage_bytes / 1024 / 1024",
                            "legendFormat": "Memory MB"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 1000}
                                ]
                            },
                            "unit": "bytes"
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                # HTTP Requests
                {
                    "id": 3,
                    "title": "HTTP Requests",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(http_requests_total[5m])",
                            "legendFormat": "{{method}} {{endpoint}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            },
                            "unit": "reqps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                # Database Connections
                {
                    "id": 4,
                    "title": "Database Connections",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "database_connections",
                            "legendFormat": "Connections"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 15},
                                    {"color": "red", "value": 20}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8}
                },
                # Redis Connections
                {
                    "id": 5,
                    "title": "Redis Connections",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "redis_connections",
                            "legendFormat": "Connections"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "yellow", "value": 8},
                                    {"color": "red", "value": 10}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 8}
                },
                # Response Time
                {
                    "id": 6,
                    "title": "Response Time",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(response_time_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(response_time_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            },
                            "unit": "s"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ]
        })
        
        return dashboard
    
    def create_business_metrics_dashboard(self) -> Dict[str, Any]:
        """Создать дашборд бизнес-метрик"""
        dashboard = self.base_config.copy()
        dashboard["dashboard"].update({
            "id": 2,
            "title": "Business Metrics",
            "tags": ["business", "metrics"],
            "panels": [
                # Total Requests
                {
                    "id": 1,
                    "title": "Total Requests",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "requests_total",
                            "legendFormat": "Total"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                # Requests by Status
                {
                    "id": 2,
                    "title": "Requests by Status",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "requests_total",
                            "legendFormat": "{{status}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                # Transactions
                {
                    "id": 3,
                    "title": "Transactions",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "transactions_total",
                            "legendFormat": "Total"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
                },
                # Active Users
                {
                    "id": 4,
                    "title": "Active Users",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "active_users",
                            "legendFormat": "{{role}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 8}
                },
                # Requests Rate
                {
                    "id": 5,
                    "title": "Requests Rate",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(requests_total[5m])",
                            "legendFormat": "{{status}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None}
                                ]
                            },
                            "unit": "reqps"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 6, "y": 8}
                }
            ]
        })
        
        return dashboard
    
    def create_security_dashboard(self) -> Dict[str, Any]:
        """Создать дашборд безопасности"""
        dashboard = self.base_config.copy()
        dashboard["dashboard"].update({
            "id": 3,
            "title": "Security Dashboard",
            "tags": ["security", "monitoring"],
            "panels": [
                # Login Attempts
                {
                    "id": 1,
                    "title": "Login Attempts",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "login_attempts_total",
                            "legendFormat": "{{status}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 10}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                # Security Violations
                {
                    "id": 2,
                    "title": "Security Violations",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "security_violations_total",
                            "legendFormat": "{{type}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 1}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0}
                },
                # Error Rate
                {
                    "id": 3,
                    "title": "Error Rate",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(errors_total[5m])",
                            "legendFormat": "{{type}}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 0.1}
                                ]
                            },
                            "unit": "errors/s"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                }
            ]
        })
        
        return dashboard
    
    def create_performance_dashboard(self) -> Dict[str, Any]:
        """Создать дашборд производительности"""
        dashboard = self.base_config.copy()
        dashboard["dashboard"].update({
            "id": 4,
            "title": "Performance Dashboard",
            "tags": ["performance", "monitoring"],
            "panels": [
                # Cache Hit Rate
                {
                    "id": 1,
                    "title": "Cache Hit Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m])) * 100",
                            "legendFormat": "Hit Rate %"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "displayMode": "gradient",
                                "orientation": "auto",
                                "reduceOptions": {
                                    "calcs": ["lastNotNull"],
                                    "fields": "",
                                    "values": False
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "red", "value": None},
                                    {"color": "yellow", "value": 80},
                                    {"color": "green", "value": 95}
                                ]
                            },
                            "unit": "percent"
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                # Database Query Duration
                {
                    "id": 2,
                    "title": "Database Query Duration",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(database_query_duration_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 1}
                                ]
                            },
                            "unit": "s"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
                },
                # HTTP Request Duration
                {
                    "id": 3,
                    "title": "HTTP Request Duration",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "95th percentile"
                        },
                        {
                            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
                            "legendFormat": "50th percentile"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 10,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "vis": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "never",
                                "spanNulls": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholds": []
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {"color": "green", "value": None},
                                    {"color": "red", "value": 1}
                                ]
                            },
                            "unit": "s"
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                }
            ]
        })
        
        return dashboard
    
    def generate_all_dashboards(self) -> List[Dict[str, Any]]:
        """Генерировать все дашборды"""
        dashboards = [
            self.create_system_overview_dashboard(),
            self.create_business_metrics_dashboard(),
            self.create_security_dashboard(),
            self.create_performance_dashboard()
        ]
        return dashboards
    
    def save_dashboards_to_files(self, output_dir: str = "grafana_dashboards"):
        """Сохранить дашборды в файлы"""
        os.makedirs(output_dir, exist_ok=True)
        
        dashboards = self.generate_all_dashboards()
        
        for i, dashboard in enumerate(dashboards):
            filename = f"{output_dir}/dashboard_{i+1}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dashboard, f, indent=2, ensure_ascii=False)
            print(f"Dashboard saved: {filename}")
        
        # Создать файл с инструкциями
        instructions = {
            "setup_instructions": {
                "prometheus": {
                    "url": "http://localhost:8001/metrics",
                    "port": 8001
                },
                "grafana": {
                    "url": "http://localhost:3000",
                    "default_credentials": {
                        "username": "admin",
                        "password": "admin"
                    }
                },
                "dashboards": [
                    "System Overview - Общий обзор системы",
                    "Business Metrics - Бизнес-метрики",
                    "Security Dashboard - Безопасность",
                    "Performance Dashboard - Производительность"
                ]
            }
        }
        
        with open(f"{output_dir}/setup_instructions.json", 'w', encoding='utf-8') as f:
            json.dump(instructions, f, indent=2, ensure_ascii=False)
        
        print(f"Setup instructions saved: {output_dir}/setup_instructions.json")


def main():
    """Основная функция"""
    print("Generating Grafana dashboards...")
    
    generator = GrafanaDashboardGenerator()
    generator.save_dashboards_to_files()
    
    print("\n✅ All dashboards generated successfully!")
    print("\n📋 Next steps:")
    print("1. Install Prometheus and configure it to scrape metrics from http://localhost:8001/metrics")
    print("2. Install Grafana and import the generated dashboard JSON files")
    print("3. Configure data source in Grafana to point to Prometheus")
    print("4. Start the metrics server: python prometheus_integration.py")


if __name__ == "__main__":
    main() 