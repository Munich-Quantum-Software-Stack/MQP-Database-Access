
from eliot import add_destinations
import os
from . import budgets, feedback, jobs, resources, status, tokens, users, db_config


if os.getenv("QUANTUM_DB_TESTING") is None:
    from eliot.journald import JournaldDestination

if os.getenv("QUANTUM_DB_TESTING") is None:
    add_destinations(JournaldDestination())


def create_app():
    app = db_config.app
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