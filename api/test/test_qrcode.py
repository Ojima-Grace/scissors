import unittest
from unittest.mock import patch
from flask import url_for
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from werkzeug.security import generate_password_hash
from ..models.qrcode import Qrcode
from ..models.analytics import Analytic
from ..models.shorturl import Shorturl
from ..models.user import User
from datetime import datetime
from http import HTTPStatus
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies
import json
from flask import Flask

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

    def test_generate_qrcode(self):
        test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com')
        db.session.add(test_user)
        db.session.commit()

        access_token = create_access_token(identity=test_user.firstname)

        short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
        db.session.add(short_url)
        db.session.commit()

        data = {
            "short_url": "abc123"
        }
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = self.client.post('/qrcode/generate', json=data, headers=headers)
        assert response.status_code == 200

    def test_qrcode_image(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com')
         db.session.add(test_user)
         db.session.commit()

         access_token = create_access_token(identity=test_user.firstname)

         short_url = Shorturl(short_url='abc123', long_url='https://example.com', user=test_user.id, click_count=0)
         db.session.add(short_url)
         db.session.commit()

         qrcode_entry = Qrcode(short_url_id=short_url.id, user_id=test_user.id, qr_identifier='123456', image=b'qr_code_image_data')
         db.session.add(qrcode_entry)
         db.session.commit()

         headers = {
             'Authorization': f'Bearer {access_token}'
         }

         response = self.client.get('/qrcode/abc123', headers=headers)
         self.assertEqual(response.status_code, 200)
         self.assertEqual(response.content_type, 'image/png')
         self.assertIn('Content-Disposition', response.headers)
         self.assertEqual(response.headers['Content-Disposition'], 'attachment; filename=qrcode.png')
         self.assertEqual(response.data, b'qr_code_image_data')
