import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# обавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# спользуем прямое подключение к 
DATABASE_URL = "postgresql://postgres:123@localhost/crm_db"

def check_roles():
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # роверяем роли
        result = db.execute(text("SELECT name FROM roles"))
        roles = result.fetchall()
        print("оли в :")
        for role in roles:
            print(f"  - {role[0]}")
        
        # роверяем пользователей с ролью callcenter
        result = db.execute(text("""
            SELECT u.username, r.name as role_name 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE r.name = 
'
callcenter
'

        """))
        callcenter_users = result.fetchall()
        print(f"\nользователи с ролью callcenter: {len(callcenter_users)}")
        for user in callcenter_users:
            print(f"  - {user[0]} (роль: {user[1]})")
            
        db.close()
        
    except Exception as e:
        print(f"шибка: {e}")

if __name__ == "__main__":
    check_roles()
