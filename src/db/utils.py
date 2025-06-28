import subprocess
from src.db.config import DatabaseConfig
from typing import Optional, List

def get_table_list():
    """
    Obtiene la lista de tablas en la base de datos.
    
    Returns:
        list: Lista de nombres de tablas
    """
    db_params = DatabaseConfig.get_connection_params()
    command = [
        "mysql",
        f"--host={db_params['host']}",
        f"--user={db_params['user']}",
        f"--password={db_params['password']}",
        db_params['database'],
        "-N",  # No mostrar headers
        "-e",  # Ejecutar comando
        "SHOW TABLES;"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip().split('\n')

def get_table_structure(table_name):
    """
    Obtiene la estructura CREATE TABLE de una tabla.
    
    Args:
        table_name (str): Nombre de la tabla
        
    Returns:
        str: Comando CREATE TABLE
    """
    db_params = DatabaseConfig.get_connection_params()
    command = [
        "mysql",
        f"--host={db_params['host']}",
        f"--user={db_params['user']}",
        f"--password={db_params['password']}",
        db_params['database'],
        "-N",
        "-e",
        f"SHOW CREATE TABLE {table_name};"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.split('\t')[1]

def get_table_data(table_name):
    """
    Obtiene los datos de una tabla en formato INSERT.
    
    Args:
        table_name (str): Nombre de la tabla
        
    Returns:
        str: Comandos INSERT
    """
    db_params = DatabaseConfig.get_connection_params()
    command = [
        "mysql",
        f"--host={db_params['host']}",
        f"--user={db_params['user']}",
        f"--password={db_params['password']}",
        db_params['database'],
        "-e",
        f"SELECT * FROM {table_name};"
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    rows = result.stdout.strip().split('\n')[1:]  # Ignorar header
    
    if not rows:
        return ""
        
    # Convertir datos a INSERT statements
    inserts = []
    for row in rows:
        values = [f"'{val}'" if val else "NULL" for val in row.split('\t')]
        inserts.append(f"INSERT INTO `{table_name}` VALUES ({','.join(values)});")
    
    return '\n'.join(inserts)

def show_table_data(table_name):
    """
    Muestra los datos actuales de una tabla.
    
    Args:
        table_name (str): Nombre de la tabla
        
    Returns:
        bool: True si se mostraron los datos correctamente, False en caso de error
    """
    try:
        db_params = DatabaseConfig.get_connection_params()
        command = [
            "mysql",
            f"--host={db_params['host']}",
            f"--user={db_params['user']}",
            f"--password={db_params['password']}",
            db_params['database'],
            "-e",
            f"SELECT * FROM {table_name};"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"\nEstado actual de la tabla {table_name}:")
        
        # Formatear la salida para que sea más legible
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            columns = lines[0].split('\t')
            data = [line.split('\t') for line in lines[1:]]
            widths = [max(len(str(row[i])) for row in [columns] + data) for i in range(len(columns))]
            
            # Imprimir el encabezado
            header = "  ".join(f"{col:<{width}}" for col, width in zip(columns, widths))
            print(header)
            print("-" * len(header))
            
            # Imprimir los datos
            for row in data:
                print("  ".join(f"{str(val):<{width}}" for val, width in zip(row, widths)))
        else:
            print("La tabla está vacía")
        print("\n")
        return True
        
    except Exception as e:
        print(f"Error al mostrar los datos de la tabla {table_name}: {e}")
        return False

def execute_query(query: str, capture_output: bool = True, additional_args: Optional[List[str]] = None) -> Optional[str]:
    """
    Ejecuta una consulta SQL en la base de datos.
    
    Args:
        query (str): Consulta SQL a ejecutar
        capture_output (bool): Si es True, captura y retorna la salida
        additional_args (list): Lista de argumentos adicionales para mysql
        
    Returns:
        str: Resultado de la consulta si capture_output es True
        None: Si capture_output es False
    
    Raises:
        subprocess.CalledProcessError: Si hay un error ejecutando la consulta
        Exception: Para otros errores inesperados
    """
    db_params = DatabaseConfig.get_connection_params()
    command = [
        "mysql",
        f"--host={db_params['host']}",
        f"--user={db_params['user']}",
        f"--password={db_params['password']}",
        db_params['database']
    ]
    
    if additional_args:
        command.extend(additional_args)
        
    command.extend(["-e", query])
    
    if capture_output:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout if result.stdout else ""
    else:
        subprocess.run(command, check=True)
        return None 