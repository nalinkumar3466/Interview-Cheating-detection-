from __future__ import with_statement
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.models.interview import Interview
from app.models.question import Question
from app.models.canvas_response import CanvasResponse
from app.models.recording import Recording
from app.models.candidate_log import CandidateLog
from app.models.interview_analysis import InterviewAnalysis

# ensure backend package is importable
here = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(here, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Import your application's models and metadata
try:
    from app.core.database import Base
except Exception:
    sys.path.insert(0, os.path.abspath(os.path.join(project_root, '..')))
    from app.core.database import Base

target_metadata = Base.metadata


def get_url():
    # Prefer DATABASE_URL env var, then alembic.ini. Do not fall back to SQLite.
    url = os.environ.get('DATABASE_URL')
    if url:
        return url
    url = config.get_main_option('sqlalchemy.url')
    if url and url != 'driver://user:pass@localhost/dbname':
        return url
    raise RuntimeError("Database URL not configured for migrations. Set the DATABASE_URL environment variable or configure sqlalchemy.url in alembic.ini")


def run_migrations_offline():
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
