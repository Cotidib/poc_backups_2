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

## Notas Importantes

- Los backups se almacenan en la carpeta `backups/`
- El script maneja automáticamente la estructura de la base de datos
- Se incluyen transacciones y manejo de llaves foráneas
- La restauración es completamente automatizada
- El sistema soporta tanto backups completos como incrementales 