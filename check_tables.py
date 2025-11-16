"""
Script para ver la estructura de las tablas users y usuarios
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Cargar variables de entorno
load_dotenv()

def check_table_structure():
    """Verifica la estructura de las tablas"""
    try:
        # Obtener DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        
        # Crear engine
        engine = create_engine(
            database_url,
            echo=False,
            connect_args={
                "ssl": {"check_hostname": False, "verify_mode": False}
            }
        )
        
        # Probar conexión
        with engine.connect() as conn:
            # Ver estructura de users
            print("=" * 60)
            print("📋 Estructura de la tabla 'users':")
            print("=" * 60)
            result = conn.execute(text("DESCRIBE users"))
            for row in result:
                print(f"  {row[0]:<20} {row[1]:<20} {row[2]:<5} {row[3]:<5}")
            
            print("\n" + "=" * 60)
            print("📋 Estructura de la tabla 'usuarios':")
            print("=" * 60)
            result = conn.execute(text("DESCRIBE usuarios"))
            for row in result:
                print(f"  {row[0]:<20} {row[1]:<20} {row[2]:<5} {row[3]:<5}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    check_table_structure()
