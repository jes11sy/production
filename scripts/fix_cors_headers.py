#!/usr/bin/env python3
"""
Скрипт для автоматического исправления hardcoded CORS headers в API файлах backend
Заменяет localhost:3000 на использование cors_utils
"""

import os
import re
import sys
from pathlib import Path

def add_cors_import(file_content: str) -> str:
    """Добавляет импорт cors_utils если его нет"""
    if "from ..core.cors_utils import" in file_content:
        return file_content
    
    # Найти место для вставки импорта (после других imports)
    lines = file_content.split('\n')
    insert_index = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from ..core.') and 'cors_utils' not in line:
            insert_index = i + 1
        elif line.startswith('router = ') or line.startswith('@router'):
            break
    
    lines.insert(insert_index, "from ..core.cors_utils import create_cors_response, get_cors_headers")
    return '\n'.join(lines)

def replace_simple_jsonresponse_cors(content: str) -> str:
    """Заменяет простые JSONResponse с CORS headers на create_cors_response"""
    # Паттерн для простых OPTIONS handlers
    pattern = r'return JSONResponse\(\s*content=\{\},\s*headers=\{\s*"Access-Control-Allow-Origin": "http://localhost:3000",\s*"Access-Control-Allow-Methods": "([^"]+)",\s*"Access-Control-Allow-Headers": "[^"]+",\s*"Access-Control-Allow-Credentials": "[^"]+",?\s*\}\s*\)'
    
    def replacement(match):
        methods = match.group(1)
        return f'return create_cors_response(allowed_methods="{methods}")'
    
    return re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

def replace_jsonresponse_with_content(content: str) -> str:
    """Заменяет JSONResponse с content и CORS headers"""
    # Паттерн для JSONResponse с контентом
    pattern = r'return JSONResponse\(\s*content=([^,]+),\s*headers=\{\s*"Access-Control-Allow-Origin": "http://localhost:3000",\s*"Access-Control-Allow-Methods": "([^"]+)",\s*"Access-Control-Allow-Headers": "[^"]+",\s*"Access-Control-Allow-Credentials": "[^"]+",?\s*\}\s*\)'
    
    def replacement(match):
        content_part = match.group(1)
        methods = match.group(2)
        return f'cors_headers = get_cors_headers("{methods}")\n    return JSONResponse(content={content_part}, headers=cors_headers)'
    
    return re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

def replace_headers_assignment(content: str) -> str:
    """Заменяет прямое присваивание CORS headers"""
    # Паттерн для response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    content = re.sub(
        r'response\.headers\["Access-Control-Allow-Origin"\] = "http://localhost:3000"',
        '# CORS headers will be set by middleware or cors_utils',
        content
    )
    
    # Убираем остальные hardcoded CORS assignments
    content = re.sub(
        r'response\.headers\["Access-Control-Allow-[^"]+"\] = "[^"]*"[\s\n]*',
        '',
        content
    )
    
    return content

def fix_file(file_path: Path) -> bool:
    """Исправляет CORS headers в одном файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Добавляем импорт
        content = add_cors_import(content)
        
        # Заменяем различные паттерны CORS headers
        content = replace_simple_jsonresponse_cors(content)
        content = replace_jsonresponse_with_content(content)
        content = replace_headers_assignment(content)
        
        # Если есть изменения, записываем файл
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed CORS headers in {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed in {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Основная функция"""
    # Определяем путь к backend/app/api
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent / "backend"
    api_dir = backend_dir / "app" / "api"
    
    if not api_dir.exists():
        print(f"❌ API directory not found: {api_dir}")
        sys.exit(1)
    
    print("🔧 Fixing CORS headers in API files...")
    
    # Файлы для обработки
    api_files = [
        "auth.py",
        "users.py", 
        "requests.py",
        "transactions.py"
    ]
    
    fixed_count = 0
    
    for file_name in api_files:
        file_path = api_dir / file_name
        if file_path.exists():
            if fix_file(file_path):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n✨ Completed! Fixed {fixed_count} files")
    print("\n🔍 Next steps:")
    print("1. Test the application to ensure CORS works correctly")
    print("2. Update any remaining hardcoded localhost references")
    print("3. Check frontend rspack.config.cjs for dev proxy settings")

if __name__ == "__main__":
    main() 