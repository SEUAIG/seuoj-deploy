.PHONY: ensure_dirs copy_dev_assets build run up dev_build dev_run dev_up down dev_down clean_data init

NAME ?=
COMPOSE_PRO = docker compose -f docker-compose.base.yml -f docker-compose.pro.yml $(if $(NAME),-p $(NAME),)
COMPOSE_DEV = docker compose -f docker-compose.base.yml -f docker-compose.dev.yml $(if $(NAME),-p $(NAME),)

ensure_dirs:
	bash ./scripts/ensure_dirs.sh

copy_dev_assets: ensure_dirs
	bash ./scripts/copy_dev_assets.sh

# ---------- 生产环境 ----------

build: ensure_dirs
	$(COMPOSE_PRO) build

run: ensure_dirs
	$(COMPOSE_PRO) up -d

up: build
	$(COMPOSE_PRO) up -d

down:
	$(COMPOSE_PRO) down

# ---------- 开发环境 ----------

dev_build: ensure_dirs
	$(COMPOSE_DEV) build

dev_run: copy_dev_assets
	$(COMPOSE_DEV) up -d

dev_up: dev_build copy_dev_assets
	$(COMPOSE_DEV) up -d

dev_down:
	$(COMPOSE_DEV) down

# ---------- 通用 ----------

clean_data:
	bash ./scripts/clean_data.sh

init:
	git submodule update --init --recursive
	cp .env.example .env
	cp agent_config.yaml.example agent_config.yaml