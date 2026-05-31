create_migration nome:
    docker compose run --rm api alembic revision --autogenerate -m "{{nome}}"

migrate:
    docker compose run --rm api alembic upgrade head
