"""Create a flask blueprint with a simple GET method route."""
from flask import Blueprint  # pragma: no cover


class Endpoint:
    """Example class for API blueprint."""

    def __init__(self):  # pragma: no cover
        """Instantiate the endpoint with the blueprints."""
        self.example_blueprint = Blueprint("example_blueprint", __name__)

        @self.example_blueprint.route("/hello_world")
        def hello():
            """Simple API request returning hello world."""
            return "Hello World!"

    @staticmethod
    def simple_method(input_num: int) -> int:
        """Simple method to test."""
        return input_num + 1
