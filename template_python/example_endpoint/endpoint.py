from flask import Blueprint


class Endpoint:
    def __init__(self):
        self.example_blueprint = Blueprint('example_blueprint', __name__)

        @self.example_blueprint.route('/hello_world')
        def hello():
            return 'Hello World!'
