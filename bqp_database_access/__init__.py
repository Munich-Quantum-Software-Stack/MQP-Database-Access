# bqp_database_access/__init__.py

from eliot import add_destinations
import os

if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination


if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


from importlib import import_module

from ._database import open_database

_EXPOSE = {
    "open_database",
    "users",
    "jobs",
    "tokens",
    "resources",
    "feedbacks",
    "request_access",
    "db_config",
    "_database",
    "_constants",
}

__all__ = list(_EXPOSE)

def __getattr__(name: str):
    if name == "open_database":
        return open_database
    if name in _EXPOSE:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def create_app():
    from . import config, login, tokens, jobs, resources, feedbacks, request_access # Ege
    app = config.app
    try:
        app.register_blueprint(login.BLUEPRINT)
        app.register_blueprint(tokens.BLUEPRINT)
        app.register_blueprint(jobs.BLUEPRINT)
        app.register_blueprint(resources.BLUEPRINT)
        app.register_blueprint(feedbacks.BLUEPRINT)
        app.register_blueprint(request_access.BLUEPRINT)
    except:
        pass
    return app
