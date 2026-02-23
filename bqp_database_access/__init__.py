from . import budgets, db_config, feedback, jobs, resources, status, tokens, users

def create_app():
    """
    Compatibility app factory for integrations expecting this symbol.
    """

    return getattr(db_config, "app", None)