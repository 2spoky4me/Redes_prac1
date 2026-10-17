
# Archivos Docker Compose
DEV_COMPOSE = docker-compose.dev.yml
PROD_COMPOSE = docker-compose.prod.yml

# Variables de entorno
DEV_ENV = .env.dev
PROD_ENV = .env.prod

.PHONY: build up-dev up-prod down down-dev down-prod \
        rebuild-dev rebuild-prod logs-dev logs-prod \
        ps ps-dev ps-prod stop-db-dev start-db-dev \
        stop-db-prod start-db-prod clean

# ---------- GENERAL ----------

# Construir las imágenes de ambos entornos
build:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) build
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) build

# Detener y eliminar los contenedores de ambos entornos
# sin borrar los volúmenes
down: down-dev down-prod

# Mostrar todos los contenedores
ps:
	docker ps -a


# ---------- DESARROLLO ----------

up-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) up -d --build

down-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) down --remove-orphans

stop-db-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) stop db_dev

start-db-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) start db_dev

rebuild-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) build --no-cache
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) up -d

logs-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) logs -f

ps-dev:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) ps


# ---------- PRODUCCIÓN ----------

up-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) up -d --build

down-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) down --remove-orphans

stop-db-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) stop db_prod

start-db-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) start db_prod

rebuild-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) build --no-cache
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) up -d

logs-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) logs -f

ps-prod:
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) ps


# ---------- LIMPIEZA ----------

# Elimina contenedores, redes y volúmenes de la práctica
# ATENCIÓN: elimina los datos persistentes de PostgreSQL
clean:
	docker compose --env-file $(DEV_ENV) -f $(DEV_COMPOSE) down --remove-orphans -v
	docker compose --env-file $(PROD_ENV) -f $(PROD_COMPOSE) down --remove-orphans -v
