"""Entrypoint for a flask application to run."""
from flask import Flask  # pragma: no cover

from template_python.example_endpoint.endpoint import Endpoint  # pragma: no cover


def main():  # pragma: no cover

    app = Flask(__name__)
    my_endpoint = Endpoint()
    app.register_blueprint(my_endpoint.example_blueprint)

    app.run(port=8080)


if __name__ == "__main__":  # pragma: no cover
    main()

