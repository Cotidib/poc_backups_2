"""
Módulo de configuración de la base de datos.
Contiene las credenciales y configuración para conectarse a MySQL.
"""

class DatabaseConfig:
    # Configuración de la base de datos
    HOST = "localhost"  # Nombre del servicio en docker-compose
    USER = "test_user"
    PASSWORD = "test_password"
    DATABASE = "test_db"

    @staticmethod
    def get_connection_params():
        """
        Retorna los parámetros de conexión como un diccionario.
        
        Returns:
            dict: Diccionario con los parámetros de conexión (host, user, password, database)
        """
        return {
            'host': 'db',  # Nombre del servicio en docker-compose
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_db'
        } 