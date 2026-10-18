
# Archivos Docker Compose
DEV_COMPOSE = docker-compose.dev.yml
PROD_COMPOSE = docker-compose.prod.yml

# Variables de entorno
DEV_ENV = .env.dev
PROD_ENV = .env.prod

.PHONY: build up-dev up-prod down down-dev down-prod \
        ps ps-dev ps-prod \
        remove-db-dev recreate-db-dev \
        remove-db-prod recreate-db-prod \
        stop-cache start-cache clean


# ---------- GENERAL ----------

# Construir las imágenes de ambos entornos
build:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) build
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) build

# Detener y eliminar ambos entornos sin borrar los volúmenes
down: down-dev down-prod

# Mostrar todos los contenedores
ps:
	docker ps -a


# ---------- DESARROLLO ----------

# Levantar DEV (Flask + PostgreSQL)
up-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) up -d --build

# Detener y eliminar DEV sin borrar los volúmenes
down-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) down --remove-orphans

# Mostrar los contenedores de DEV
ps-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) ps


# ---------- PRODUCCIÓN ----------

# Levantar PROD (Flask + PostgreSQL + Redis)
up-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) up -d --build

# Detener y eliminar PROD sin borrar los volúmenes
down-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) down --remove-orphans

# Mostrar los contenedores de PROD
ps-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) ps


# ---------- PRUEBAS DE PERSISTENCIA ----------

# Eliminar PostgreSQL DEV sin borrar el volumen
remove-db-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) rm -s -f db_dev

# Crear un nuevo contenedor PostgreSQL DEV reutilizando el volumen
recreate-db-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) up -d --no-deps db_dev

# Eliminar PostgreSQL PROD sin borrar el volumen
remove-db-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) rm -s -f db_prod

# Crear un nuevo contenedor PostgreSQL PROD reutilizando el volumen
recreate-db-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) up -d --no-deps db_prod


# ---------- PRUEBAS DE REDIS ----------

# Detener Redis para comprobar /status
stop-cache:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) stop cache

# Iniciar Redis para comprobar la recuperación
start-cache:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) start cache


# ---------- LIMPIEZA ----------

# Eliminar contenedores, redes y volúmenes de ambos entornos
# ATENCIÓN: se perderán los datos de PostgreSQL
clean:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) down --remove-orphans -v
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) down --remove-orphans -v
