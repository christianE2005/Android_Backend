"""
Script de prueba para verificar la conexión a la base de datos MySQL
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Cargar variables de entorno
load_dotenv()

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    try:
        # Obtener DATABASE_URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ Error: DATABASE_URL no está configurada")
            return False
        
        # Convertir mysql:// a mysql+pymysql://
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        
        print(f"🔗 Conectando a la base de datos...")
        print(f"   Host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'N/A'}")
        
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
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Conexión exitosa! Test query result: {row[0]}")
            
            # Obtener versión de la base de datos
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()
            print(f"📊 MySQL Version: {version[0]}")
            
            # Listar tablas
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📋 Tablas en la base de datos:")
                for table in tables:
                    print(f"   - {table[0]}")
                    
                # Si existe la tabla users, mostrar info
                if any('users' in str(table) for table in tables):
                    result = conn.execute(text("SELECT COUNT(*) FROM users"))
                    count = result.fetchone()
                    print(f"\n👥 Total de usuarios en la tabla 'users': {count[0]}")
            else:
                print("\n📋 No hay tablas en la base de datos aún")
            
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST DE CONEXIÓN A LA BASE DE DATOS")
    print("=" * 60)
    print()
    
    success = test_database_connection()
    
    print()
    print("=" * 60)
    if success:
        print("✅ PRUEBA EXITOSA - La base de datos está funcionando correctamente")
    else:
        print("❌ PRUEBA FALLIDA - Revisa la configuración de DATABASE_URL")
    print("=" * 60)
