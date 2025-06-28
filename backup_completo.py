import os
import subprocess
import time
from datetime import datetime
from db_config import DatabaseConfig
from db_utils import get_table_list, get_table_structure, get_table_data, show_table_data, execute_query
from disaster_simulator import simulate_disaster, verify_disaster_simulation

def save_backup_position(position):
    """Guarda la posición actual del binary log"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    with open(os.path.join(backup_dir, 'last_position.txt'), 'w') as f:
        f.write(position)

def get_binary_log_position():
    """Obtiene la posición actual del binary log"""
    result = execute_query("SHOW MASTER STATUS;")
    if result and len(result.strip().split('\n')) > 1:
        # El resultado tiene este formato:
        # File    Position    Binlog_Do_DB    Binlog_Ignore_DB    Executed_Gtid_Set
        # mysql-bin.000001    1234            ...
        fields = result.strip().split('\n')[1].split('\t')
        return f"{fields[0]}:{fields[1]}"
    return None

def create_full_backup():
    """
    Crea un backup completo de la base de datos.
    El archivo de backup se guarda en el directorio 'backups' con un timestamp.
    
    Returns:
        tuple: (ruta del archivo de backup, posición del binary log) o (None, None) si hubo un error
    """
    try:
        # Crear directorio de backups si no existe
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Generar nombre del archivo de backup con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f"backup_completo_{timestamp}.sql")
        
        db_params = DatabaseConfig.get_connection_params()
        
        with open(backup_file, 'w') as f:
            # Escribir metadata
            f.write(f"-- Backup de la base de datos {db_params['database']}\n")
            f.write(f"-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Configuración inicial
            f.write("SET FOREIGN_KEY_CHECKS=0;\n")
            f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n")
            f.write("SET AUTOCOMMIT = 0;\n")
            f.write("START TRANSACTION;\n\n")
            
            # Obtener y procesar cada tabla
            tables = get_table_list()
            for table in tables:
                f.write(f"--\n-- Estructura de la tabla `{table}`\n--\n\n")
                f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                f.write(f"{get_table_structure(table)};\n\n")
                
                f.write(f"--\n-- Datos de la tabla `{table}`\n--\n\n")
                table_data = get_table_data(table)
                if table_data:
                    f.write(f"{table_data}\n\n")
            
            # Configuración final
            f.write("COMMIT;\n")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        
        # Obtener y guardar la posición del binary log
        binary_log_pos = get_binary_log_position()
        if binary_log_pos:
            save_backup_position(binary_log_pos)
            print(f"Posición del binary log guardada: {binary_log_pos}")
        else:
            print("Advertencia: No se pudo obtener la posición del binary log")
        
        print(f"Backup creado exitosamente: {backup_file}")
        return backup_file, binary_log_pos
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None, None

def restore_full_backup(backup_file):
    """
    Restaura la base de datos desde un archivo de backup.
    
    Args:
        backup_file (str): Ruta al archivo de backup
        
    Returns:
        bool: True si la restauración fue exitosa, False en caso contrario
    """
    try:
        if not os.path.exists(backup_file):
            print(f"Error: El archivo de backup {backup_file} no existe")
            return False
            
        print(f"\nRestaurando backup desde: {backup_file}")
        
        db_params = DatabaseConfig.get_connection_params()
        command = [
            "mysql",
            f"--host={db_params['host']}",
            f"--user={db_params['user']}",
            f"--password={db_params['password']}",
            db_params['database']
        ]
        
        with open(backup_file, 'r') as f:
            process = subprocess.run(
                command,
                input=f.read(),
                text=True,
                check=True
            )
        
        print("Restauración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def main():
    """
    Función principal que ejecuta el proceso completo de backup, simulación de desastre y restauración.
    """
    print("=== Sistema de Backup y Restauración ===")
    time.sleep(1)
    
    # Mostrar datos iniciales
    print("\nEstado inicial de la base de datos:")
    time.sleep(2)
    for table in get_table_list():
        show_table_data(table)
        time.sleep(1)
    
    # Paso 1: Crear backup
    print("\n1. Creando backup...")
    time.sleep(2)
    backup_file, binary_log_pos = create_full_backup()
    if not backup_file:
        print("Error: No se pudo crear el backup")
        return
    
    print(f"Backup completo creado: {backup_file}")
    if binary_log_pos:
        print(f"Posición del binary log: {binary_log_pos}")
    
    time.sleep(4)
        
    # Paso 2: Simular desastre
    print("\n2. Simulando desastre...")
    time.sleep(2)
    success, results = simulate_disaster()
    if not success:
        print("Error: No se pudo simular el desastre")
        return
    
    # Verificar el estado después del desastre
    verification = verify_disaster_simulation()
    if verification:
        print("\nVerificación del desastre:")
        print(f"- Tablas vaciadas: {', '.join(verification['empty_tables'])}")
        if verification['non_empty_tables']:
            print("¡Advertencia! Algunas tablas aún contienen datos:")
            for table_info in verification['non_empty_tables']:
                print(f"  - {table_info['table']}: {table_info['count']} registros")
        if verification['error_tables']:
            print("Errores en tablas:")
            for error_info in verification['error_tables']:
                print(f"  - {error_info['table']}: {error_info['error']}")
    
    time.sleep(4)
        
    # Paso 3: Restaurar desde backup
    print("\n3. Restaurando desde backup...")
    time.sleep(2)
    if not restore_full_backup(backup_file):
        print("Error: No se pudo restaurar el backup")
        return
    
    # Mostrar estado final
    print("\nEstado final después de la restauración:")
    time.sleep(2)
    for table in get_table_list():
        show_table_data(table)
        time.sleep(1)
    
    time.sleep(2)
    print("\n¡Proceso completado exitosamente!")

if __name__ == "__main__":
    main() 