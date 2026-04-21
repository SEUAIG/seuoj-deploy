.PHONY: ensure_dirs copy_dev_assets run run_dev

NAME ?=

ensure_dirs:
	bash ./scripts/ensure_dirs.sh

copy_dev_assets: ensure_dirs
	bash ./scripts/copy_dev_assets.sh

run: ensure_dirs
	docker compose $(if $(NAME),-p $(NAME),) up -d --build

dev_run: copy_dev_assets
	docker compose $(if $(NAME),-p $(NAME),) up -d --build

clean_data:
	bash ./scripts/clean_data.sh

down:
	docker compose $(if $(NAME),-p $(NAME),) down
