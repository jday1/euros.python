"""Create a flask blueprint with a simple GET method route."""
from flask import Blueprint  # pragma: no cover


class Endpoint:  # pragma: no cover
    """Example class for API blueprint."""
    def __init__(self):
        self.example_blueprint = Blueprint("example_blueprint", __name__)

        @self.example_blueprint.route("/hello_world")
        def hello():
            return "Hello World!"
