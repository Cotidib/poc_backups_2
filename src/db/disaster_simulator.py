import subprocess
from src.db.config import DatabaseConfig
from src.db.utils import get_table_list, execute_query

def simulate_disaster(tables=None, operation="TRUNCATE"):
    """
    Simula un desastre en la base de datos.
    
    Args:
        tables (list): Lista de tablas a afectar. Si es None, afecta a todas las tablas.
        operation (str): Operación a realizar ("TRUNCATE", "DROP"). Por defecto es "TRUNCATE".
    
    Returns:
        bool: True si la simulación fue exitosa, False en caso contrario
        dict: Diccionario con detalles de la operación
    """
    try:
        # Si no se especifican tablas, obtener todas
        if tables is None:
            tables = get_table_list()
        
        print("\nSimulando desastre...")
        print(f"Operación a realizar: {operation}")
        
        results = {
            'success': True,
            'affected_tables': [],
            'failed_tables': [],
            'operation': operation
        }
        
        for table in tables:
            try:
                if operation.upper() == "TRUNCATE":
                    query = f"TRUNCATE TABLE {table};"
                elif operation.upper() == "DROP":
                    query = f"DROP TABLE {table};"
                else:
                    raise ValueError(f"Operación no soportada: {operation}")
                
                execute_query(query, capture_output=False)
                print(f"- Tabla {table}: {operation} ejecutado correctamente")
                results['affected_tables'].append(table)
                
            except subprocess.CalledProcessError as e:
                print(f"- Error en tabla {table}: {e}")
                results['failed_tables'].append({
                    'table': table,
                    'error': str(e)
                })
                results['success'] = False
        
        print("Simulación de desastre completada")
        return results['success'], results
        
    except Exception as e:
        print(f"Error inesperado durante la simulación: {e}")
        return False, {
            'success': False,
            'error': str(e),
            'affected_tables': [],
            'failed_tables': [],
            'operation': operation
        }

def verify_disaster_simulation(tables=None):
    """
    Verifica el estado de las tablas después de una simulación de desastre.
    
    Args:
        tables (list): Lista de tablas a verificar. Si es None, verifica todas las tablas.
    
    Returns:
        dict: Diccionario con el estado de cada tabla
    """
    try:
        if tables is None:
            tables = get_table_list()
            
        results = {
            'empty_tables': [],
            'non_empty_tables': [],
            'error_tables': []
        }
        
        for table in tables:
            try:
                # Usar -N para obtener solo el número sin encabezado
                result = execute_query(
                    f"SELECT COUNT(*) FROM {table};",
                    capture_output=True,
                    additional_args=["-N"]
                )
                
                if result is None:
                    raise ValueError("No se pudo obtener el conteo de la tabla")
                    
                # La consulta siempre devolverá un string, incluso si está vacío
                count = int(result.strip() or "0")
                
                if count == 0:
                    results['empty_tables'].append(table)
                else:
                    results['non_empty_tables'].append({
                        'table': table,
                        'count': count
                    })
                    
            except (subprocess.CalledProcessError, ValueError) as e:
                results['error_tables'].append({
                    'table': table,
                    'error': str(e)
                })
        
        return results
        
    except Exception as e:
        print(f"Error durante la verificación: {e}")
        return None 