"""
Script de prueba para verificar conexiones
"""

from config import settings
from redis_client import redis_client
from sqlalchemy import create_engine, text

def test_database():
    """Probar conexión a Supabase"""
    print("🔍 Probando conexión a Supabase...")
    try:
        db_url = settings.get_database_url()
        # Ocultar contraseña en el log
        safe_url = db_url.split('@')[1] if '@' in db_url else db_url
        print(f"   URL: postgresql://***@{safe_url}")
        
        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   ✅ Conexión exitosa!")
            print(f"   PostgreSQL: {version[:50]}...")
            return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_redis():
    """Probar conexión a Redis"""
    print("\n🔍 Probando conexión a Redis...")
    try:
        if settings.is_upstash_redis():
            print(f"   Tipo: Upstash Redis (REST API)")
            print(f"   URL: {settings.UPSTASH_REDIS_REST_URL}")
        else:
            print(f"   Tipo: Redis Local")
            print(f"   Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        if redis_client.ping():
            print(f"   ✅ Conexión exitosa!")
            
            # Probar operación básica
            test_key = "test:connection"
            redis_client.set(test_key, "ok", ex=10)
            value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            if value == "ok":
                print(f"   ✅ Operaciones básicas funcionando!")
            return True
        else:
            print(f"   ❌ No se pudo conectar")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PRUEBA DE CONEXIONES")
    print("=" * 50)
    
    db_ok = test_database()
    redis_ok = test_redis()
    
    print("\n" + "=" * 50)
    if db_ok and redis_ok:
        print("✅ Todas las conexiones funcionan correctamente!")
    else:
        print("❌ Algunas conexiones fallaron. Revisa tu configuración.")
    print("=" * 50)

