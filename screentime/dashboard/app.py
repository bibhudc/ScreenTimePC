"""
Flask application factory for the ScreenTimePC dashboard.
"""

from pathlib import Path

from flask import Flask
from screentime.db.repository import Repository

DASHBOARD_DIR = Path(__file__).resolve().parent


def create_app(repository: Repository) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(DASHBOARD_DIR / "static"),
        template_folder=str(DASHBOARD_DIR / "templates"),
    )
    app.config["REPOSITORY"] = repository

    from screentime.dashboard.routes import bp
    app.register_blueprint(bp)

    return app
