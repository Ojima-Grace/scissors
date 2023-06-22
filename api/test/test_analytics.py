import unittest
from unittest.mock import patch
from flask import url_for
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from werkzeug.security import generate_password_hash
from ..models.analytics import Analytic
from ..models.shorturl import Shorturl
from ..models.user import User
from datetime import datetime
from http import HTTPStatus
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies
import json

def serialize_user(user):
        return {
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname,
            'email': user.email
        }

class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config=config_dict['test'])
        self.appctx = self.app.app_context()
        self.appctx.push()
        self.client = self.app.test_client()
        self.app.config['SERVER_NAME'] = 'localhost:5000'  # Set the SERVER_NAME configuration
        db.create_all()

    def tearDown(self):
        db.drop_all()

        self.appctx.pop()
        self.app = None
        self.client = None

    def test_get_url_analytics(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com')
         db.session.add(test_user)
         db.session.commit()

         access_token = create_access_token(identity=test_user.firstname)

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         analytic_entry = Analytic(short_url_id=short_url.id, click_timestamp=datetime.now(), ip_address='127.0.0.1', user_agent='Test User Agent')
         db.session.add(analytic_entry)
         db.session.commit()

         headers = {
             'Authorization': f'Bearer {access_token}'
         }

         response = self.client.get('/analytics/analytics/abc123', headers=headers)
         self.assertEqual(response.status_code, 200)

         expected_data = {
             'analytics': [
                 {
                     'short_url': 'abc123',
                     'long_url': 'https://example.com',
                     'click_timestamp': analytic_entry.click_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                     'ip_address': '127.0.0.1',
                     'user_agent': 'Test User Agent'
                 }
             ]
         }
         self.assertEqual(response.json, expected_data)
