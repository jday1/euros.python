"""Entrypoint for a flask application to run."""
from flask import Flask  # pragma: no cover

from template_python.example_endpoint.endpoint import Endpoint  # pragma: no cover


def create_app() -> Flask:  # pragma: no cover
    """Create the app, registering the blueprints."""
    app: Flask = Flask(__name__)
    my_endpoint = Endpoint()
    app.register_blueprint(my_endpoint.example_blueprint)

    return app


main_app = create_app()  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    main_app.run(port=8080)
