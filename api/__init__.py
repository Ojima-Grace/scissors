from flask import Flask
from flask_restx import Api
from .auth.views import auth_namespace
from .shorturl.views import shorturl_namespace
from .analytics.views import analytics_namespace
from .qrcode.views import qrcode_namespace
from .config.config import config_dict
from .utils import db
from .models.user import User
from .models.shorturl import Shorturl
from .models.analytics import Analytic
from .models.qrcode import Qrcode
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import NotFound, MethodNotAllowed
from .config.config import config_dict, cache, limiter
import redis

def create_app(config=config_dict['test']):
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    db.init_app(app)
    cache.init_app(app)
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    limiter.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)
    authorizations = {
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Add a JWT token to the header with Bearer &lt;JWT&gt; token to authorize **"
        }
    }
    api = Api(app,
              title="URL SHORTENER AND QR-CODE GENERATOR API",
              description="A REST API FOR SHORTENING A URL AND GENERATING A QR-CODE FOR THAT SHORTENED URL",
              authorizations=authorizations,
              security='Bearer Auth'
              )
    api.add_namespace(auth_namespace, path='/auth')
    api.add_namespace(shorturl_namespace, path='/shorturl')
    api.add_namespace(analytics_namespace, path='/analytics')
    api.add_namespace(qrcode_namespace, path='/qrcode')

    @api.errorhandler(NotFound)
    def not_found(error):
        return {"error": "Not Found"}, 404
    
    @api.errorhandler(MethodNotAllowed)
    def method_not_allowed(error):
        return {"error": "Message Not Allowed"}, 405

    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'user': User,
            'shorturl': Shorturl,
            'analytic': Analytic,
            'qrcode': Qrcode,
        }       
    return app