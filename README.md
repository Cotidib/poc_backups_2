# Sistema de Backup MySQL con Docker

Este proyecto implementa un sistema de backup para bases de datos MySQL utilizando Docker y Python.

## Estructura del Proyecto

```
.
├── docker-compose.yml
├── Dockerfile
├── backup_completo.py
├── db_config.py
├── init.sql
├── requirements.txt
└── README.md
```

## Configuración

1. Asegúrate de tener Docker y Docker Compose instalados
2. Clona este repositorio
3. Configura las variables de entorno en el archivo `docker-compose.yml`

## Uso

1. Inicia los contenedores:
```bash
docker-compose up -d
```

2. Ejecuta el script de backup:
```bash
docker exec python-backup python backup_completo.py
```

## Verificación

Para verificar que el backup se realizó correctamente:

1. Revisa los archivos de backup generados en la carpeta `backups/`
2. Verifica la integridad de los datos restaurados
3. Comprueba los logs del contenedor Python:
```bash
docker logs python-backup
```

## Solución de Problemas

Si encuentras algún problema:

1. Verifica que los contenedores estén corriendo:
```bash
docker-compose ps
```

2. Revisa los logs de los contenedores:
```bash
docker logs mysql-db
docker logs python-backup
```

3. Asegúrate de que las credenciales en `db_config.py` sean correctas

## Notas Importantes

- Los backups se almacenan en la carpeta `backups/`
- El script maneja automáticamente la estructura de la base de datos
- Se incluyen transacciones y manejo de llaves foráneas
- La restauración es completamente automatizada 