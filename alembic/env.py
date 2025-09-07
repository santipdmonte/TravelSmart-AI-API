# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context

# Importa la Base declarativa principal y todos los modelos para que se registren
import models
from database import Base

# Configura Alembic para que use los metadatos de la Base principal,
# que ahora contiene todas tus tablas.
config = context.config
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def include_object(object, name, type_, reflected, compare_to):
    """
    Ignora las tablas internas del sistema de la base de datos durante la autogeneración.
    """
    if type_ == "table" and (name.startswith("edb$") or name == "callback_queue_table"):
        return False
    return True

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,  # Añadido para offline también
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            dialect_opts={"paramstyle": "named"}
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()