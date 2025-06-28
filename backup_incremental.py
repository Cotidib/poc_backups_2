import os
import subprocess
from datetime import datetime
from db_config import DatabaseConfig
from db_utils import execute_query, get_table_list, get_table_structure, get_table_data, show_table_data
import time
from typing import Optional, Tuple

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
    Crea un backup incremental basado en los cambios desde el último backup
    Returns:
        tuple: (nombre_archivo_backup, posicion_inicio, posicion_fin)
    """
    # Obtener la última posición de backup
    last_position = get_last_backup_position()
    if not last_position:
        print("No se encontró un backup previo. Se requiere un backup completo primero.")
        return None, None, None

    # Obtener la posición actual
    current_position = get_binary_log_position()
    if not current_position:
        print("No se pudo obtener la posición actual del binary log")
        return None, None, None

    # Crear el archivo de backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/backup_incremental_{timestamp}.sql'
    
    # Obtener los cambios desde la última posición
    last_file, last_pos = last_position.split(':')
    current_file, current_pos = current_position.split(':')
    
    with open(backup_file, 'w') as f:
        f.write(f"-- Backup incremental generado el {datetime.now()}\n")
        f.write(f"-- Desde: {last_position}\n")
        f.write(f"-- Hasta: {current_position}\n\n")
        
        try:
            # Obtener eventos del binary log usando SHOW BINLOG EVENTS
            query = f"""
            SHOW BINLOG EVENTS 
            IN '{last_file}'
            FROM {last_pos}
            LIMIT 10000;
            """
            
            print("\nObteniendo eventos del binary log...")
            result = execute_query(query)
            
            if not result:
                print("No se pudieron obtener los eventos del binary log")
                return None, None, None
            
            # Procesar y filtrar los eventos
            events = []
            for line in result.strip().split('\n')[1:]:  # Saltar el header
                fields = line.split('\t')
                if len(fields) >= 6:  # Log_name, Pos, Event_type, Server_id, End_log_pos, Info
                    event_type = fields[2]
                    info = fields[5]
                    
                    # Solo incluir eventos relevantes (INSERT, UPDATE, DELETE, etc.)
                    if any(x in event_type.upper() for x in ['QUERY', 'TABLE_MAP', 'WRITE_ROWS', 'UPDATE_ROWS', 'DELETE_ROWS']):
                        if 'BEGIN' not in info and 'COMMIT' not in info:
                            events.append(info)
            
            # Escribir los eventos al archivo
            if events:
                f.write('\n'.join(events))
                f.write('\n')
            else:
                f.write('-- No se encontraron cambios relevantes\n')
            
            # Guardar la nueva posición
            save_backup_position(current_position)
            
            return backup_file, last_position, current_position
            
        except Exception as e:
            print(f"Error creando backup incremental: {e}")
            return None, None, None

def main():
    print("\n=== Sistema de Backup Incremental ===\n")
    
    print("Realizando cambios de prueba en la base de datos...\n")

    # 1. Actualizar un empleado existente
    print("1. Actualizando empleado existente...")
    result = execute_query(
        "UPDATE employees SET position = 'Senior Developer' WHERE name = 'Juan Pérez'"
    )
    if result is not None:
        print("✓ Empleado actualizado correctamente\n")
    else:
        print("✗ Error al actualizar empleado\n")

    # 2. Insertar un nuevo empleado
    print("2. Insertando nuevo empleado...")
    result = execute_query(
        "INSERT INTO employees (name, position) VALUES ('Carlos López', 'Data Scientist')"
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
        # print(f"Posición inicial: {start_pos}")
        # print(f"Posición final: {end_pos}\n")

        print("Contenido del archivo de backup:")
        with open(backup_file, 'r') as f:
            print(f.read())
    else:
        print("\n✗ Error: No se pudo crear el backup incremental")
        print("Asegúrate de haber realizado un backup completo primero")

if __name__ == "__main__":
    main() 