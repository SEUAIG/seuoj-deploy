.PHONY: ensure_dirs copy_dev_assets run dev_run

NAME ?=

ensure_dirs:
	bash ./scripts/ensure_dirs.sh

copy_dev_assets: ensure_dirs
	bash ./scripts/copy_dev_assets.sh

run: ensure_dirs
	docker compose -f docker-compose.base.yml -f docker-compose.pro.yml $(if $(NAME),-p $(NAME),) up -d --build

dev_run: copy_dev_assets
	docker compose -f docker-compose.base.yml -f docker-compose.dev.yml $(if $(NAME),-p $(NAME),) up -d --build

clean_data:
	bash ./scripts/clean_data.sh

down:
	docker compose -f docker-compose.base.yml -f docker-compose.pro.yml $(if $(NAME),-p $(NAME),) down

dev_down:
	docker compose -f docker-compose.base.yml -f docker-compose.dev.yml $(if $(NAME),-p $(NAME),) down
