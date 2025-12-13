"""
Script para ejecutar el script SQL de roles y permisos en Supabase
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Cargar variables de entorno del backend
load_dotenv(dotenv_path='../backend/.env')

def ejecutar_script_sql():
    """Ejecutar el script SQL de roles y permisos"""
    
    # Obtener URL de conexión desde variables de entorno
    # Usa el usuario postgres principal (no el usuario_api)
    supabase_url = os.getenv('SUPABASE_DB_URL')
    
    if not supabase_url:
        print("❌ Error: No se encontró SUPABASE_DB_URL en las variables de entorno")
        print("   Asegúrate de tener un archivo .env en el directorio backend/")
        return False
    
    # Reemplazar el usuario en la URL con 'postgres' (usuario administrador)
    # Esto es necesario para crear usuarios y roles
    if 'postgres.ywgbzwjkwkabcdhgmntg' in supabase_url:
        # Extraer la contraseña y el host
        parts = supabase_url.split('@')
        if len(parts) == 2:
            password_part = parts[0].split(':')[-1]
            host_part = parts[1]
            admin_url = f"postgresql://postgres:{password_part}@{host_part}"
        else:
            print("❌ Error: No se pudo parsear la URL de conexión")
            return False
    else:
        # Si ya es postgres, usar directamente
        admin_url = supabase_url.replace('usuario_api', 'postgres').replace('postgres.ywgbzwjkwkabcdhgmntg', 'postgres')
    
    print("=" * 60)
    print("EJECUTANDO SCRIPT DE ROLES Y PERMISOS")
    print("=" * 60)
    print(f"Conectando a Supabase...")
    print(f"URL: postgresql://postgres:***@{admin_url.split('@')[1] if '@' in admin_url else 'N/A'}")
    print()
    
    try:
        # Leer el script SQL
        script_path = os.path.join(os.path.dirname(__file__), '02_dcl_roles_permisos.sql')
        
        if not os.path.exists(script_path):
            print(f"❌ Error: No se encontró el archivo {script_path}")
            return False
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_sql = f.read()
        
        print("📄 Script SQL cargado correctamente")
        print()
        
        # Conectar a la base de datos
        engine = create_engine(admin_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Ejecutar el script completo
            print("🔄 Ejecutando script SQL...")
            print()
            
            # Dividir el script en comandos individuales
            # PostgreSQL requiere ejecutar comandos uno por uno
            comandos = [cmd.strip() for cmd in script_sql.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            for i, comando in enumerate(comandos, 1):
                if comando:
                    try:
                        # Ejecutar cada comando
                        conn.execute(text(comando))
                        conn.commit()
                        print(f"✅ Comando {i} ejecutado")
                    except Exception as e:
                        # Algunos errores son esperados (IF NOT EXISTS)
                        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                            print(f"⚠️  Comando {i}: Ya existe (ignorado)")
                        else:
                            print(f"❌ Error en comando {i}: {str(e)}")
                            print(f"   Comando: {comando[:100]}...")
            
            print()
            print("=" * 60)
            print("✅ Script ejecutado correctamente")
            print("=" * 60)
            print()
            print("Usuarios creados:")
            print("  - usuario_api (contraseña: api_secure_password_2024!)")
            print("  - usuario_batch (contraseña: batch_secure_password_2024!)")
            print()
            print("Ahora puedes configurar tu .env del batch-worker con:")
            print("  SUPABASE_DB_URL_BATCH=postgresql://usuario_batch:batch_secure_password_2024!@aws-0-us-west-2.pooler.supabase.com:5432/postgres")
            print()
            
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando el script: {str(e)}")
        print()
        print("💡 Alternativa: Ejecuta el script manualmente en el SQL Editor de Supabase")
        print("   1. Ve a tu proyecto en Supabase")
        print("   2. Abre 'SQL Editor'")
        print("   3. Copia y pega el contenido de database/02_dcl_roles_permisos.sql")
        print("   4. Ejecuta el script")
        return False

if __name__ == "__main__":
    print()
    print("⚠️  NOTA: Este script requiere permisos de administrador")
    print("   Si falla, ejecuta el script manualmente en el SQL Editor de Supabase")
    print()
    
    respuesta = input("¿Continuar? (s/n): ").lower()
    if respuesta != 's':
        print("Cancelado.")
        sys.exit(0)
    
    print()
    ejecutar_script_sql()

