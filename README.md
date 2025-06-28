# Sistema de Backup MySQL con Docker

Este proyecto implementa un sistema de backup para bases de datos MySQL utilizando Docker y Python.

## Configuración

1. Asegúrate de tener Docker y Docker Compose instalados
2. Clona este repositorio

## Uso

1. Construye los contenedores desde el directorio raíz del proyecto:
```bash
docker compose -f docker/docker-compose.yml build --no-cache backup
```

2. Inicia los contenedores:
```bash
docker compose -f docker/docker-compose.yml up -d
```

3. Para ejecutar un backup completo:
```bash
docker exec -w /app python-backup python3 -m src.backup.full
```

4. Para ejecutar un backup incremental (despues de haber ejecutado backup completo):
```bash
docker exec -w /app python-backup python3 -m src.backup.incremental
```

## Flujo Recomendado de Pruebas

Para garantizar un funcionamiento correcto del sistema, se recomienda seguir estrictamente este orden de ejecución:

1. **Construcción de Contenedores**:
2. **Inicio de Servicios**:
   Esperar unos segundos para que MySQL inicialice completamente.
3. **Ejecución de Backup Completo**:
   Este paso es **obligatorio** antes de realizar backups incrementales.
4. **Ejecución de Backup Incremental**:
   Solo ejecutar después de tener al menos un backup completo.

   > **📝 Nota sobre cambios simulados**: El script de backup incremental incluye simulaciones de cambios en la base de datos:
   > - Actualiza un empleado existente (`UPDATE employees SET position = 'Senior Developer' WHERE name = 'Juan Perez'`)
   > - Inserta un nuevo empleado (`INSERT INTO employees (name, position) VALUES ('Carlos Lopez', 'Data Scientist')`)
   > 
   > Si desea ejecutar el backup incremental más de una vez, necesitará modificar estas sentencias en `src/backup/incremental.py` para simular cambios diferentes. De lo contrario, no se detectarán nuevos cambios para respaldar.

> **⚠️ Importante**: Este es el único flujo que ha sido completamente probado. Otros órdenes de ejecución o escenarios no han sido validados y podrían resultar en errores o comportamientos inesperados.

## Verificación

Para verificar que el backup se realizó correctamente:

1. Revisa los archivos de backup generados en la carpeta `backups/`
2. Verifica la integridad de los datos restaurados

5. Si necesitas reconstruir los contenedores después de cambios:
```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml build --no-cache backup
docker compose -f docker/docker-compose.yml up -d
```

## Funcionamiento del Backup Completo

El backup completo realiza una copia íntegra de la base de datos, incluyendo:

1. **Estructura de las tablas**: Guarda los comandos `CREATE TABLE` y la definición completa de cada tabla.
2. **Datos**: Exporta todos los registros de cada tabla en formato SQL.
3. **Configuración de seguridad**: 
   - Deshabilita temporalmente las verificaciones de llaves foráneas
   - Utiliza transacciones para garantizar la consistencia
   - Restaura la configuración al finalizar

El proceso de backup completo:
1. Genera un archivo con timestamp en la carpeta `backups/`
2. Guarda metadata y configuración inicial
3. Para cada tabla:
   - Guarda su estructura
   - Exporta todos sus datos
4. Registra la posición del binary log para backups incrementales futuros

La restauración:
1. Lee el archivo de backup
2. Ejecuta las sentencias SQL en orden
3. Maneja automáticamente las dependencias entre tablas

## Funcionamiento del Backup Incremental

El backup incremental utiliza los binary logs de MySQL para capturar y respaldar únicamente los cambios realizados desde el último backup. Este método es más eficiente en tiempo y espacio que los backups completos.

### Binary Logs

Los binary logs son archivos que registran todos los cambios realizados en la base de datos. En este proyecto:

1. **Configuración**: Los binary logs están configurados en modo ROW:
   ```
   --log-bin=/var/lib/mysql/mysql-bin.log --binlog-format=ROW
   ```
   - El modo ROW garantiza que se registren los cambios exactos en cada fila
   - Cada evento se registra con su posición exacta en el log

2. **Funcionamiento**:
   - Cada operación (INSERT, UPDATE, DELETE) se registra secuencialmente
   - Se mantiene un registro de la posición actual en el archivo `last_position.txt`
   - Los logs permiten reproducir los cambios en el orden exacto en que ocurrieron

### Proceso de Backup Incremental

1. **Inicio**:
   - Verifica la existencia de un backup completo previo
   - Lee la última posición respaldada del binary log
   - Obtiene la posición actual del binary log

2. **Creación del Backup**:
   - Utiliza `mysqlbinlog` para extraer los cambios entre las dos posiciones
   - Maneja automáticamente cambios entre múltiples archivos de log
   - Genera un archivo SQL con los cambios incrementales

   > **¿Cómo funciona el manejo de múltiples archivos de log?**  
   > MySQL genera múltiples archivos de binary log (ejemplo: mysql-bin.000001, mysql-bin.000002) para mejor gestión. El sistema:
   > - **Caso Simple**: Si los cambios están en un mismo archivo, extrae directamente desde la posición inicial hasta la final
   > - **Caso Múltiple**: Si los cambios cruzan archivos:
   >   1. Extrae desde la última posición hasta el final del archivo antiguo
   >   2. Extrae desde el inicio hasta la posición actual en el archivo nuevo
   >   3. Combina los cambios manteniendo el orden cronológico
   > 
   > Esto garantiza que no se pierdan cambios cuando MySQL rota sus archivos de log y es completamente transparente para el usuario.

3. **Restauración**:
   - Restaura primero el último backup completo
   - Aplica los cambios incrementales en orden cronológico
   - Garantiza la consistencia de los datos

### Ventajas

- Reduce significativamente el tiempo de backup
- Minimiza el espacio de almacenamiento necesario
- Permite la recuperación punto a punto (PITR)
- Mantiene un historial detallado de cambios

## Notas Importantes

- Los backups se almacenan en la carpeta `backups/`
- El script maneja automáticamente la estructura de la base de datos
- Se incluyen transacciones y manejo de llaves foráneas
- La restauración es completamente automatizada
- El sistema soporta tanto backups completos como incrementales 