from flask import Flask

from template_python.example_endpoint.endpoint import Endpoint

app = Flask(__name__)

my_endpoint = Endpoint()

app.register_blueprint(my_endpoint.example_blueprint)

if __name__ == '__main__':
    app.run(port=8080)
