
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    from webapp.routes import init_routes
    init_routes(app)
    return app
