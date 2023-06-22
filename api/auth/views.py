from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from ..models.user import User
from ..config.config import cache, limiter
from ..utils import db
from werkzeug.security import generate_password_hash, check_password_hash
from http import HTTPStatus
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, unset_jwt_cookies
import json

auth_namespace = Namespace('auth', description='name space for authentication')

signup_model = auth_namespace.model(
    'Signup', {
        'id': fields.Integer(),
        'username': fields.String(required=True, description="A Username"),
        'email': fields.String(required=True, description="An Email"),
        'password': fields.String(required=True, description="A Password"),  
    }
)

user_model = auth_namespace.model(
    'User', {
        'id': fields.Integer(),
        'username': fields.String(required=True, description="A Username"),
        'email': fields.String(required=True, description="An Email"),
        'password_hash': fields.String(required=True, description="A Password"),
    }    
)

login_model = auth_namespace.model(
    'Login', {
        'email': fields.String(required=True, description="An Email"),
        'password': fields.String(required=True, description="A Password"),  
    }
)

@auth_namespace.route('/signup')
class SignUp(Resource):
    @limiter.limit("10 per minute")
    @auth_namespace.expect(signup_model)
    #@auth_namespace.marshal_with(user_model)
    @auth_namespace.doc(
            description='Signup A User'
    )
    def post(self):
        """
          Signup a User  
        """
        data = request.get_json()
        data = auth_namespace.payload
        
        username = data['username']
        email = data['email']
        password_hash = generate_password_hash(data["password"])
        
        # new_user = User.query.filter_by(firstname=firstname).first()
        # if new_user:
        #      return {'message': 'User already exists'}, 400
        username_exists = User.query.filter_by(username=username).first()
        if username_exists:
            return {'message': 'Username already taken'}, 400
        
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            return {'message': 'User with this email already exists'}, 400
        
        new_user = User(
            username = username,
            email = email,
            #password_hash = generate_password_hash(data.get('password'))
            password_hash = password_hash
        )

        new_user.save()

        response_data = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'password_hash': new_user.password_hash
        }

        #return json.dumps(response_data), 201, {'Content-Type': 'application/json'} #HTTPStatus.CREATED
        #return {new_user: 'new_user'}, HTTPStatus.CREATED
        return {"message": "Account created successfully, please log in"}, 201

@auth_namespace.route('/login')
class Login(Resource):
    @auth_namespace.expect(login_model)
    @auth_namespace.doc(
            description='Login A User'
    )
    @cache.cached(timeout=60)
    def post(self):
        """
           Generate JWT Token

        """
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if (user is not None) and check_password_hash(user.password_hash,password):
            access_token = create_access_token(identity=user.username)
            refresh_token = create_refresh_token(identity=user.username)

            response = {
                'access_token': access_token,
                'refresh_token': refresh_token
            }

            return response, HTTPStatus.OK

@auth_namespace.route('/refresh')
class Refresh(Resource):
    @auth_namespace.doc(
            description='Generate Refresh Token'
    )
    @jwt_required(refresh=True)
    def post(self):
        """

            Generate Refresh Token

        """
        username = get_jwt_identity()

        access_token = create_access_token(identity=username)

        return {'access_token': access_token}, HTTPStatus.OK

@auth_namespace.route('/logout')
class Logout(Resource):
    @auth_namespace.doc(
            description='Logout A User'
    )
    @jwt_required()
    def post(self):
        """
           
           Logout A User

        """
        unset_jwt_cookies
        db.session.commit()
        return {"Message": "You're now logged out!"}, HTTPStatus.OK