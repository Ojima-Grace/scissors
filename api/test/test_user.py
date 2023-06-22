import unittest
from .. import create_app
from ..config.config import config_dict
from ..utils import db
from werkzeug.security import generate_password_hash
from ..models.user import User
from http import HTTPStatus
import json


class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config=config_dict['test'])
        self.appctx = self.app.app_context()
        self.appctx.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.drop_all()

        self.appctx.pop()
        self.app = None
        self.client = None

    def test_user_registration(self):
        data = {
            "firstname": "testuser",
            "lastname": "testuserlastname",
            "email": "testuser@gmail",
            "password": "password"
        }

        response = self.client.post('/auth/signup', json=data)
        assert response.status_code == 201

        response_data = response.get_json()
        assert response_data is not None
        assert response_data['id'] is not None
        assert response_data['firstname'] == "testuser"
        assert response_data['lastname'] == "testuserlastname"
        assert response_data['email'] == "testuser@gmail"

    def test_user_login(self):
         test_user = User(firstname='testuser', lastname='testuser', email='testuser@gmail.com', password_hash=generate_password_hash('password'))
         db.session.add(test_user)
         db.session.commit()

         data = {
             "email": "testuser@gmail.com",
             "password": "password"
         }
         response = self.client.post('/auth/login', json=data)

         assert response.status_code == 200
         assert 'access_token' in response.json
         assert 'refresh_token' in response.json