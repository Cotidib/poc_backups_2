import os
import subprocess
from datetime import datetime
from src.db.config import DatabaseConfig
from src.db.utils import execute_query, get_table_list, get_table_structure, get_table_data, show_table_data
import time
from typing import Optional, Tuple
from src.db.disaster_simulator import simulate_disaster
from src.backup.full import restore_full_backup

def get_binary_log_info():
    """
    Obtiene información sobre la posición actual del binary log.
    
    Returns:
        tuple: (nombre del archivo binlog actual, posición)
    """
    result = execute_query("SHOW MASTER STATUS;")
    if not result:
        raise Exception("No se pudo obtener información del binary log")
        
    # El resultado tiene este formato:
    # File    Position    Binlog_Do_DB    Binlog_Ignore_DB    Executed_Gtid_Set
    # mysql-bin.000001    1234            ...
    lines = result.strip().split('\n')
    if len(lines) < 2:  # necesitamos al menos el header y una línea de datos
        raise Exception("No hay información de binary log disponible")
        
    fields = lines[1].split('\t')
    if len(fields) < 2:
        raise Exception("Formato de binary log inesperado")
        
    return fields[0], int(fields[1])

def enable_binary_logging():
    """
    Habilita el binary logging si no está habilitado.
    """
    try:
        # Verificar si binary logging está habilitado
        result = execute_query("SHOW VARIABLES LIKE 'log_bin';")
        if result is None:
            raise Exception("No se pudo verificar el estado del binary logging")
            
        is_enabled = 'ON' in result.upper()
        
        if not is_enabled:
            print("Binary logging no está habilitado. Habilitando...")
            # En un entorno real, esto requeriría modificar my.cnf y reiniciar MySQL
            # Por ahora, solo mostraremos un mensaje
            print("ADVERTENCIA: En un entorno real, necesitarías:")
            print("1. Modificar my.cnf para agregar:")
            print("   log_bin = mysql-bin")
            print("   server-id = 1")
            print("2. Reiniciar el servidor MySQL")
            raise Exception("Binary logging debe estar habilitado para backups incrementales")
            
    except Exception as e:
        print(f"Error verificando binary logging: {e}")
        raise

def get_last_backup_position() -> Optional[str]:
    """
    Lee la última posición de backup guardada
    Returns:
        str: Última posición en formato 'file:position'
    """
    try:
        with open('backups/last_position.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error leyendo última posición de backup: {e}")
        return None

def save_backup_position(position: str) -> bool:
    """
    Guarda la posición actual del backup
    Args:
        position (str): Posición en formato 'file:position'
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        with open('backups/last_position.txt', 'w') as f:
            f.write(position)
        return True
    except Exception as e:
        print(f"Error guardando posición de backup: {e}")
        return False

def get_binary_log_position() -> Optional[str]:
    """
    Obtiene la posición actual del binary log
    Returns:
        str: Posición en formato 'file:position'
    """
    try:
        result = execute_query("SHOW MASTER STATUS")
        if not result:
            return None
            
        print("Obteniendo posición del binary log...")
        print(f"Resultado de SHOW MASTER STATUS: '{result}'")
        
        # Parsear el resultado
        lines = result.strip().split('\n')
        print(f"Líneas encontradas: {len(lines)}")
        for i, line in enumerate(lines):
            print(f"Línea {i}: '{line}'")
            
        if len(lines) < 2:
            return None
            
        # La segunda línea contiene los datos
        fields = lines[1].split()
        print(f"Campos encontrados: {len(fields)}")
        for i, field in enumerate(fields[:2]):  # Solo mostrar los primeros dos campos
            print(f"Campo {i}: '{field}'")
            
        if len(fields) < 2:
            return None
            
        position = f"{fields[0]}:{fields[1]}"
        print(f"Posición del binary log: {position}\n")
        return position
        
    except Exception as e:
        print(f"Error obteniendo posición del binary log: {e}")
        return None

def create_incremental_backup() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Crea un backup incremental válido usando mysqlbinlog.
    Returns:
        tuple: (nombre_archivo_backup, posicion_inicio, posicion_fin)
    """
    # Obtener la última posición
    last_position = get_last_backup_position()
    if not last_position:
        print("No se encontró un backup previo. Se requiere un backup completo primero.")
        return None, None, None

    # Obtener la posición actual
    current_position = get_binary_log_position()
    if not current_position:
        print("No se pudo obtener la posición actual del binary log.")
        return None, None, None

    last_file, last_pos = last_position.split(':')
    current_file, current_pos = current_position.split(':')

    # Nombre del archivo backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/backup_incremental_{timestamp}.sql'

    print(f"Creando backup incremental desde {last_position} hasta {current_position}")

    try:
        # Caso sencillo: ambos en el mismo archivo binlog
        if last_file == current_file:
            cmd = [
                "mysqlbinlog",
                f"--start-position={last_pos}",
                f"--stop-position={current_pos}",
                f"/var/lib/mysql/{last_file}"
            ]
            with open(backup_file, "w") as f:
                subprocess.run(cmd, stdout=f, check=True)
        
        else:
            # Caso donde se cruzó de archivo binlog
            print(f"Detectado cambio de archivo binlog de {last_file} a {current_file}")
            
            # Extraer desde last_file desde last_pos hasta el final
            cmd1 = [
                "mysqlbinlog",
                f"--start-position={last_pos}",
                f"/var/lib/mysql/{last_file}"
            ]
            # Extraer archivos intermedios si los hubiera (no implementado aquí)

            # Extraer desde el inicio del current_file hasta current_pos
            cmd2 = [
                "mysqlbinlog",
                f"--stop-position={current_pos}",
                f"/var/lib/mysql/{current_file}"
            ]
            with open(backup_file, "w") as f:
                subprocess.run(cmd1, stdout=f, check=True)
                subprocess.run(cmd2, stdout=f, check=True)

        print(f"Backup incremental creado: {backup_file}")
        
        # Guardar la nueva posición
        save_backup_position(current_position)

        return backup_file, last_position, current_position
    
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando mysqlbinlog: {e}")
        return None, None, None

def restore_incremental_backup(backup_file: str) -> bool:
    """
    Restaura un backup incremental aplicando el archivo generado por mysqlbinlog.
    Este proceso incluye primero restaurar el último backup completo y luego aplicar
    los cambios incrementales.

    Args:
        backup_file (str): Ruta al archivo incremental .sql

    Returns:
        bool: True si se restauró correctamente, False si hubo errores.
    """
    print(f"\nIniciando proceso de restauración completa + incremental\n")

    # Validar archivo incremental
    if not os.path.isfile(backup_file):
        print(f"✗ Error: el archivo {backup_file} no existe.")
        return False

    # Primero encontrar y restaurar el último backup completo
    print("\n=== Paso 1: Restaurando el último backup completo ===")
    backup_dir = "backups"
    full_backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_completo_")]
    if not full_backups:
        print("✗ Error: No se encontró un backup completo")
        return False
    
    latest_full_backup = os.path.join(backup_dir, sorted(full_backups)[-1])
    print(f"Restaurando desde: {latest_full_backup}")
    
    if not restore_full_backup(latest_full_backup):
        print("✗ Error al restaurar el backup completo")
        return False
    
    print("✓ Backup completo restaurado correctamente")

    # Ahora restaurar el backup incremental
    print("\n=== Paso 2: Aplicando backup incremental ===")
    
    # Leer configuración de conexión
    db_params = DatabaseConfig.get_connection_params()
    cmd = [
        "mysql",
        f"--host={db_params['host']}",
        f"--user={db_params['user']}",
        f"--password={db_params['password']}",
        f"--port={db_params['port']}",
        db_params['database'],
    ]

    try:
        with open(backup_file, "r") as f:
            subprocess.run(cmd, stdin=f, check=True)
        print("✓ Backup incremental restaurado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error restaurando el backup incremental: {e}")
        return False

def main():
    print("\n=== Sistema de Backup Incremental ===\n")
    
    print("Realizando cambios de prueba en la base de datos...\n")

    # 1. Actualizar un empleado existente
    print("1. Actualizando empleado existente...")
    result = execute_query(
        "UPDATE employees SET position = 'Senior Developer' WHERE name = 'Juan Perez'"
    )
    if result is not None:
        print("✓ Empleado actualizado correctamente\n")
    else:
        print("✗ Error al actualizar empleado\n")

    # 2. Insertar un nuevo empleado
    print("2. Insertando nuevo empleado...")
    result = execute_query(
        "INSERT INTO employees (name, position) VALUES ('Carlos Lopez', 'Data Scientist')"
    )
    if result is not None:
        print("✓ Nuevo empleado insertado correctamente\n")
    else:
        print("✗ Error al insertar empleado\n")

    # Mostrar el estado actual de la tabla
    print("\nEstado actual de la tabla employees:")
    if not show_table_data('employees'):
        print("✗ Error al mostrar los datos de la tabla\n")

    # Esperar un momento antes de hacer el backup
    print("\nEsperando un momento antes de hacer el backup...\n")
    time.sleep(1)

    # Crear el backup incremental
    print("Creando backup incremental...\n")
    backup_file, start_pos, end_pos = create_incremental_backup()
    if backup_file:
        print("\n✓ Backup incremental creado exitosamente")
        print(f"Archivo de backup: {backup_file}")
        print(f"Posición inicial: {start_pos}")
        print(f"Posición final: {end_pos}\n")

        # Simular un desastre
        print("\n=== Simulando un desastre en la base de datos ===")
        success, results = simulate_disaster()
        if success:
            print("✓ Desastre simulado correctamente")
            print("\nEstado de la tabla después del desastre:")
            show_table_data('employees')
        else:
            print("✗ Error al simular el desastre")
            return

        # Restaurar usando el backup incremental (que incluye restaurar el backup completo)
        print("\n=== Iniciando proceso de restauración ===")
        if restore_incremental_backup(backup_file):
            print("\nEstado final de la tabla después de la restauración:")
            show_table_data('employees')
            print("\n¡Proceso completo de backup y restauración finalizado exitosamente!")
        else:
            print("✗ Error durante el proceso de restauración")
            return
    else:
        print("\n✗ Error: No se pudo crear el backup incremental")
        print("Asegúrate de haber realizado un backup completo primero")

if __name__ == "__main__":
    main() 