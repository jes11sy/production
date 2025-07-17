#!/usr/bin/env python3
"""
CLI инструмент для управления метриками
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, List
import click
from tabulate import tabulate

# Добавляем путь к приложению
sys.path.append('.')

from app.database import get_db
from app.metrics import (
    metrics_collector,
    performance_collector,
    business_collector
)


@click.group()
def cli():
    """Управление системой метрик"""
    pass


@cli.command()
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json']), help='Формат вывода')
def list_metrics(format):
    """Список всех метрик"""
    all_metrics = metrics_collector.get_all_metrics()
    
    if format == 'json':
        click.echo(json.dumps(all_metrics, indent=2, default=str))
        return
    
    # Табличный формат
    headers = ['Название', 'Тип', 'Описание', 'Единица', 'Последнее значение', 'Количество']
    rows = []
    
    for name, data in all_metrics.items():
        definition = data.get('definition')
        if definition:
            rows.append([
                name,
                definition.type.value,
                definition.description,
                definition.unit or '-',
                data.get('latest_value', '-'),
                data.get('count', 0)
            ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('metric_name')
@click.option('--since', '-s', help='Показать данные с определенной даты (YYYY-MM-DD)')
@click.option('--limit', '-l', type=int, default=10, help='Максимальное количество значений')
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json']), help='Формат вывода')
def show_metric(metric_name, since, limit, format):
    """Показать данные конкретной метрики"""
    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            click.echo(f"Неверный формат даты: {since}. Используйте YYYY-MM-DD")
            return
    
    values = metrics_collector.get_values(metric_name, since_date, limit)
    
    if not values:
        click.echo(f"Нет данных для метрики: {metric_name}")
        return
    
    if format == 'json':
        data = [
            {
                'value': v.value,
                'timestamp': v.timestamp.isoformat(),
                'tags': v.tags,
                'metadata': v.metadata
            }
            for v in values
        ]
        click.echo(json.dumps(data, indent=2))
        return
    
    # Табличный формат
    headers = ['Время', 'Значение', 'Теги', 'Метаданные']
    rows = []
    
    for value in values:
        tags_str = ', '.join([f"{k}={v}" for k, v in value.tags.items()]) if value.tags else '-'
        metadata_str = ', '.join([f"{k}={v}" for k, v in value.metadata.items()]) if value.metadata else '-'
        
        rows.append([
            value.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            value.value,
            tags_str,
            metadata_str
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('metric_name')
@click.option('--since', '-s', help='Показать статистику с определенной даты (YYYY-MM-DD)')
def stats(metric_name, since):
    """Показать статистику по метрике"""
    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            click.echo(f"Неверный формат даты: {since}. Используйте YYYY-MM-DD")
            return
    
    statistics = metrics_collector.get_statistics(metric_name, since_date)
    
    if not statistics:
        click.echo(f"Нет данных для метрики: {metric_name}")
        return
    
    click.echo(f"Статистика для метрики: {metric_name}")
    click.echo("=" * 50)
    
    for key, value in statistics.items():
        click.echo(f"{key.capitalize()}: {value}")


@cli.command()
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json']), help='Формат вывода')
def business_summary(format):
    """Сводка бизнес-метрик"""
    async def get_business_data():
        async for db in get_db():
            await business_collector.collect_all_business_metrics(db)
            break
    
    # Запускаем сбор бизнес-метрик
    asyncio.run(get_business_data())
    
    business_metrics = {
        'Общее количество заявок': metrics_collector.get_latest_value('requests_total'),
        'Общее количество транзакций': metrics_collector.get_latest_value('transactions_total'),
        'Сумма транзакций': metrics_collector.get_latest_value('transactions_amount'),
        'Активные пользователи': metrics_collector.get_latest_value('active_users'),
        'Конверсия заявок (%)': metrics_collector.get_latest_value('conversion_rate'),
        'Среднее время обработки (сек)': metrics_collector.get_latest_value('avg_processing_time'),
        'Дневная выручка': metrics_collector.get_latest_value('revenue_daily'),
        'Общее количество звонков': metrics_collector.get_latest_value('calls_total'),
        'Средняя длительность звонка (сек)': metrics_collector.get_latest_value('call_duration_avg'),
    }
    
    if format == 'json':
        click.echo(json.dumps(business_metrics, indent=2, default=str))
        return
    
    # Табличный формат
    headers = ['Метрика', 'Значение']
    rows = []
    
    for name, value in business_metrics.items():
        rows.append([name, value if value is not None else '-'])
    
    click.echo("Сводка бизнес-метрик")
    click.echo("=" * 50)
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.option('--format', '-f', default='table', type=click.Choice(['table', 'json']), help='Формат вывода')
def performance_summary(format):
    """Сводка метрик производительности"""
    # Обновляем системные метрики
    performance_collector.record_system_metrics()
    
    performance_metrics = {
        'HTTP запросы (всего)': metrics_collector.get_latest_value('http_requests_total'),
        'DB запросы (всего)': metrics_collector.get_latest_value('db_queries_total'),
        'Использование памяти (MB)': metrics_collector.get_latest_value('memory_usage'),
        'Использование CPU (%)': metrics_collector.get_latest_value('cpu_usage'),
        'Частота ошибок (%)': metrics_collector.get_latest_value('error_rate'),
        'Попадания в кэш': metrics_collector.get_latest_value('cache_hits'),
        'Промахи кэша': metrics_collector.get_latest_value('cache_misses'),
        'Активные DB соединения': metrics_collector.get_latest_value('db_connections_active'),
    }
    
    if format == 'json':
        click.echo(json.dumps(performance_metrics, indent=2, default=str))
        return
    
    # Табличный формат
    headers = ['Метрика', 'Значение']
    rows = []
    
    for name, value in performance_metrics.items():
        rows.append([name, value if value is not None else '-'])
    
    click.echo("Сводка метрик производительности")
    click.echo("=" * 50)
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('metric_name')
@click.argument('value', type=float)
@click.option('--tags', '-t', multiple=True, help='Теги в формате key=value')
def record(metric_name, value, tags):
    """Записать значение метрики"""
    tags_dict = {}
    for tag in tags:
        if '=' in tag:
            key, val = tag.split('=', 1)
            tags_dict[key] = val
    
    metrics_collector.record(metric_name, value, tags_dict)
    click.echo(f"Записано: {metric_name} = {value}")
    if tags_dict:
        click.echo(f"Теги: {tags_dict}")


@cli.command()
@click.argument('metric_name')
@click.option('--value', '-v', type=float, default=1, help='Значение для увеличения')
@click.option('--tags', '-t', multiple=True, help='Теги в формате key=value')
def increment(metric_name, value, tags):
    """Увеличить счетчик"""
    tags_dict = {}
    for tag in tags:
        if '=' in tag:
            key, val = tag.split('=', 1)
            tags_dict[key] = val
    
    metrics_collector.increment(metric_name, value, tags_dict)
    click.echo(f"Увеличено: {metric_name} на {value}")
    if tags_dict:
        click.echo(f"Теги: {tags_dict}")


@cli.command()
@click.option('--hours', '-h', type=int, default=24, help='Удалить метрики старше указанного количества часов')
@click.option('--confirm', is_flag=True, help='Подтвердить удаление без запроса')
def cleanup(hours, confirm):
    """Очистить старые метрики"""
    if not confirm:
        click.confirm(f'Удалить все метрики старше {hours} часов?', abort=True)
    
    older_than = timedelta(hours=hours)
    metrics_collector.clear_old_metrics(older_than)
    click.echo(f"Очищены метрики старше {hours} часов")


@cli.command()
@click.argument('metric_name')
@click.option('--confirm', is_flag=True, help='Подтвердить удаление без запроса')
def clear(metric_name, confirm):
    """Очистить конкретную метрику"""
    if not confirm:
        click.confirm(f'Удалить все данные метрики {metric_name}?', abort=True)
    
    with metrics_collector._lock:
        if metric_name in metrics_collector.metrics:
            metrics_collector.metrics[metric_name].clear()
            click.echo(f"Метрика {metric_name} очищена")
        else:
            click.echo(f"Метрика {metric_name} не найдена")


@cli.command()
@click.option('--output', '-o', help='Файл для сохранения экспорта')
@click.option('--metrics', '-m', multiple=True, help='Конкретные метрики для экспорта')
@click.option('--since', '-s', help='Экспортировать данные с определенной даты (YYYY-MM-DD)')
def export(output, metrics, since):
    """Экспорт метрик в JSON"""
    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            click.echo(f"Неверный формат даты: {since}. Используйте YYYY-MM-DD")
            return
    
    all_metrics = metrics_collector.get_all_metrics()
    metrics_to_export = list(metrics) if metrics else list(all_metrics.keys())
    
    result = {}
    for metric_name in metrics_to_export:
        if metric_name in all_metrics:
            values = metrics_collector.get_values(metric_name, since_date)
            result[metric_name] = {
                'definition': all_metrics[metric_name].get('definition'),
                'statistics': metrics_collector.get_statistics(metric_name, since_date),
                'values': [
                    {
                        'value': v.value,
                        'timestamp': v.timestamp.isoformat(),
                        'tags': v.tags,
                        'metadata': v.metadata
                    }
                    for v in values
                ]
            }
    
    export_data = json.dumps(result, indent=2, default=str)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(export_data)
        click.echo(f"Экспорт сохранен в: {output}")
    else:
        click.echo(export_data)


@cli.command()
def collect_all():
    """Принудительный сбор всех метрик"""
    async def collect():
        async for db in get_db():
            await business_collector.collect_all_business_metrics(db)
            break
    
    # Сбор бизнес-метрик
    asyncio.run(collect())
    
    # Сбор метрик производительности
    performance_collector.record_system_metrics()
    
    click.echo("Сбор всех метрик завершен")


@cli.command()
def dashboard():
    """Показать дашборд с основными метриками"""
    async def get_dashboard_data():
        async for db in get_db():
            await business_collector.collect_all_business_metrics(db)
            break
    
    # Обновляем данные
    asyncio.run(get_dashboard_data())
    performance_collector.record_system_metrics()
    
    # Бизнес-метрики
    click.echo("📊 ДАШБОРД МЕТРИК")
    click.echo("=" * 60)
    
    click.echo("\n🏢 БИЗНЕС-ПОКАЗАТЕЛИ:")
    click.echo("-" * 30)
    
    business_data = [
        ["Заявки (всего)", metrics_collector.get_latest_value('requests_total') or 0],
        ["Конверсия (%)", f"{metrics_collector.get_latest_value('conversion_rate') or 0:.1f}%"],
        ["Дневная выручка", f"{metrics_collector.get_latest_value('revenue_daily') or 0:.2f} ₽"],
        ["Активные пользователи", metrics_collector.get_latest_value('active_users') or 0],
        ["Транзакции (всего)", metrics_collector.get_latest_value('transactions_total') or 0],
        ["Звонки (всего)", metrics_collector.get_latest_value('calls_total') or 0],
    ]
    
    for name, value in business_data:
        click.echo(f"{name:<25} {value}")
    
    click.echo("\n⚡ ПРОИЗВОДИТЕЛЬНОСТЬ:")
    click.echo("-" * 30)
    
    performance_data = [
        ["Память (MB)", f"{metrics_collector.get_latest_value('memory_usage') or 0:.1f}"],
        ["CPU (%)", f"{metrics_collector.get_latest_value('cpu_usage') or 0:.1f}%"],
        ["HTTP запросы", metrics_collector.get_latest_value('http_requests_total') or 0],
        ["DB запросы", metrics_collector.get_latest_value('db_queries_total') or 0],
        ["Попадания в кэш", metrics_collector.get_latest_value('cache_hits') or 0],
        ["Промахи кэша", metrics_collector.get_latest_value('cache_misses') or 0],
    ]
    
    for name, value in performance_data:
        click.echo(f"{name:<25} {value}")
    
    click.echo("\n" + "=" * 60)
    click.echo(f"Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    cli() 