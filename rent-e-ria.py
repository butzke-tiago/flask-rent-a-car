import rent_a_car
import logging
from flask_migrate import upgrade


def create_app():
    app = rent_a_car.create_app()
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    with app.app_context():
        upgrade()

    return app
