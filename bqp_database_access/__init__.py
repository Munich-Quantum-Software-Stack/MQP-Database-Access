from . import budgets, feedback, jobs, resources, status, tokens, users, db_config, job_metrics


def create_app():
    """
    Compatibility app factory for integrations expecting this symbol.
    """

    return None