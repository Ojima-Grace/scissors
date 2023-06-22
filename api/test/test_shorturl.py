import unittest
from unittest.mock import patch
from flask import url_for
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from werkzeug.security import generate_password_hash
from ..models.shorturl import Shorturl
from ..models.user import User
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

    def test_url_create(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com')
         db.session.add(test_user)
         db.session.commit()

         data = {
            "long_url": "https://www.example.com",
            "short_url": "example"
         }

         access_token = create_access_token(identity=test_user.firstname)

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         headers = {
             'Authorization': f'Bearer {access_token}'
         }

         response = self.client.post('/shorturl/shorturl', json=data, headers=headers)
         response_data = response.get_json()

         self.assertEqual(response.status_code, 201)
         self.assertIsNotNone(response_data)
         self.assertIn("shortened_url", response_data)
         shortened_url = response_data["shortened_url"]
         self.assertTrue(shortened_url.startswith("http://") or shortened_url.startswith("https://"))
         self.assertTrue(shortened_url.endswith("example"))

    def test_url_redirect(self):
        short_url = 'abc123'
        long_url = 'http://example.com'
        shorturl = Shorturl(short_url=short_url, long_url=long_url)
        db.session.add(shorturl)
        db.session.commit()

        response = self.client.get(f'/shorturl/{short_url}')

        self.assertEqual(response.status_code, 302) 
        self.assertEqual(response.location, long_url)

    def test_get_click_count(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com', password_hash=generate_password_hash('password'))
         db.session.add(test_user)
         db.session.commit()

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         token = create_access_token(identity='testuser')
         headers = {'Authorization': f'Bearer {token}'}

         response = self.client.get('/shorturl/clicks/abc123', headers=headers)

         assert response.status_code == 200
         assert response.json == {'click_count': 0}


    def test_get_link_history(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com', password_hash=generate_password_hash('password'))
         db.session.add(test_user)
         db.session.commit()

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         token = create_access_token(identity='testuser')
         headers = {'Authorization': f'Bearer {token}'}

         response = self.client.get('/shorturl/link_history', headers=headers)

         assert response.status_code == 200

    def test_delet_shorturl(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com', password_hash=generate_password_hash('password'))
         db.session.add(test_user)
         db.session.commit()

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         token = create_access_token(identity='testuser')
         headers = {'Authorization': f'Bearer {token}'}

         response = self.client.delete('/shorturl/delete/abc123', headers=headers)

         assert response.status_code == 200