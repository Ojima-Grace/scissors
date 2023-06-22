from flask_restx import Namespace, Resource, fields, marshal_with
from flask import redirect, request, json, jsonify, current_app, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.user import User
from ..models.analytics import Analytic
from ..models.shorturl import Shorturl
from ..models.qrcode import Qrcode
from ..utils import db
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from http import HTTPStatus
from ..config.config import cache, limiter
import requests
import string
import random
import validators
import redis
#import tldextract

def normalize_and_canonicalize_url(url):
    parsed_url = urlparse(url)
    normalized_url = parsed_url._replace(netloc=parsed_url.netloc.replace('www.', ''), path=parsed_url.path.rstrip('/'))
    canonical_url = normalized_url._replace(scheme="http", netloc=normalized_url.netloc.lower())
    return urlunparse(canonical_url)

def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def validate_url(url):
    if not validators.url(url):
        return False
    return True

def is_valid_url(url):
    try:
        response = requests.head(url)
        return response.ok
    except requests.exceptions.RequestException:
        return False

shorturl_namespace = Namespace('shorturl', description='name space for url shortening')

shorturl_model = shorturl_namespace.model(
    'Shorturl', {
        'id': fields.Integer(),
        'longurl': fields.String(description="Long Url", required=True),
        'shorturl': fields.String(description="Short Url", required=True),
        'date_created': fields.DateTime(description="Date Created"),
        'click_count': fields.Integer(),
    }
)
createshorturl_model  = shorturl_namespace.model(
    'Createshorturl', {
        'long_url': fields.String(description="Long Url", required=True),
        'short_url': fields.String(description="Short Url")
    }
)

@shorturl_namespace.route('/shorturl')
class UrlCreate(Resource):
    @limiter.limit("10 per minute")
    @shorturl_namespace.expect(createshorturl_model)
    @shorturl_namespace.doc(
        description='Shorten A Url'
    )
    @jwt_required()
    def post(self):
        """
          Shorten Your Url  
        """
        current_user = User.query.filter_by(username=get_jwt_identity()).first()

        data = shorturl_namespace.payload
        long_url = data.get('long_url')
        short_url = data.get('short_url')
        
        #normalized_url = normalize_url(long_url)

        if not validate_url(long_url):
            return {'message': 'Invalid URL'}, 400
        
        canonical_long_url = normalize_and_canonicalize_url(long_url)
    
        base_url = request.host_url

        existing_user_shorturl = Shorturl.query.filter_by(user=current_user, long_url=canonical_long_url).first()
        if existing_user_shorturl:
            return {'message': 'URL already shortened by you'}, 400

        # existing_longurl = Shorturl.query.filter_by(long_url=canonical_long_url).first()
        # if existing_longurl:
        #     return {'message': 'URL already exists'}, 400 #HTTPStatus.BAD_REQUEST

        if not is_valid_url(canonical_long_url):
            return {'message': 'Invalid or non-existent URL'}, 400


        existing_shorturl = Shorturl.query.filter_by(short_url=short_url).first()
        if existing_shorturl:
            return {'message': 'Shortened URL name already exists, please choose another name'}#, 400 #HTTPStatus.BAD_REQUEST

        shorturl = Shorturl.query.filter_by(long_url=long_url).first()
        if shorturl:
            shortened_url = f"{base_url}{shorturl.short_url}"

        if short_url is None or short_url == "":
            short_url = generate_short_url()

            shorturl = Shorturl(
                long_url=canonical_long_url,
                short_url=short_url
            )
            shorturl.user = current_user
            shorturl.save()
        else:
            shorturl = Shorturl(
                long_url=canonical_long_url,
                short_url=short_url
            )
            shorturl.user = current_user
            shorturl.save()

        shortened_url = f"{base_url}{short_url}"

        return {'shortened_url': shortened_url}, 201 #HTTPStatus.CREATED

@shorturl_namespace.route('/<string:short_url>')
class UrlRedirect(Resource): 
  @shorturl_namespace.doc(
      description='Url Redirect',
      params = {'short_url': 'A Short URL'}
  )
  #@jwt_required() 
  @cache.cached(timeout=60)
  def get(self, short_url):

    """
      Redirect A Shortened Url to A Long Url
    """
    shorturl = Shorturl.query.filter_by(short_url=short_url).first()

    if shorturl:
        long_url = shorturl.long_url

        shorturl.click_count += 1
        db.session.commit()

        tracking_data = Analytic(
            short_url_id=shorturl.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        tracking_data.save()
        db.session.commit()

        response = make_response(redirect(long_url))
        response.status_code = 302
        return response

    response = make_response(jsonify({"message": "Url not found"}))
    response.status_code = 404
    return response

@shorturl_namespace.route('/clicks/<string:short_url>')
class GetUrlClickCount(Resource):
    @shorturl_namespace.doc(
            description='Get The Number Of Clicks Of Short URL',
            params = {'short_url': 'A Short URL'}
    )
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, short_url):
        """
        Retrieve the number of clicks for the specified short URL
        """
        current_user = User.query.filter_by(username=get_jwt_identity()).first()

        shorturl = Shorturl.query.filter_by(short_url=short_url).first()

        if not shorturl:
            return {'message': 'URL not found'}, 404
        
        if shorturl.user_id != current_user.id:
            return {'message': 'URL not found'}, 404

        click_count = shorturl.click_count

        return {'click_count': click_count}, 200

        
@shorturl_namespace.route('/link_history')
class UserLinkHistory(Resource):
    @shorturl_namespace.doc(
            description='Get All User Link History',
    )
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self):
        """
        Get all link history for the specified user
        """
        current_user = User.query.filter_by(username=get_jwt_identity()).first()

        shorturls = Shorturl.query.filter_by(user=current_user).all()
        if not shorturls:
            return {'message': 'Unauthorized'}, HTTPStatus.UNAUTHORIZED

        serialized_shorturls = []
        for shorturl in shorturls:
            serialized_shorturl = {
                'id': shorturl.id,
                'long_url': shorturl.long_url,
                'short_url': shorturl.short_url,
                'click_count': shorturl.click_count,
                'date_created': shorturl.date_created.strftime("%Y-%m-%d %H:%M:%S")
            }
            serialized_shorturls.append(serialized_shorturl)

        return serialized_shorturls, HTTPStatus.OK
    
@shorturl_namespace.route('/delete/<string:short_url>')
class UrlDelete(Resource):
    @shorturl_namespace.doc(
        description='Delete a User Specific Shortened URL',
        params = {'short_url': 'A Short URL'}
    )
    @jwt_required()
    def delete(self, short_url):
        """
          Delete a USer Specific Shortened Url
        """
        current_user = User.query.filter_by(username=get_jwt_identity()).first()
       
        shorturl = Shorturl.query.filter_by(short_url=short_url).first()
        if not shorturl:
            return {'message': 'URL not found'}, HTTPStatus.NOT_FOUND
        
        if shorturl.user_id != current_user.id:
            return {'message': 'URL not found'}, HTTPStatus.NOT_FOUND
        
        Analytic.query.filter_by(short_url_id=shorturl.id).delete()
        Qrcode.query.filter_by(short_url_id=shorturl.id).delete()

        shorturl.delete()
        db.session.commit()

        return {'message': 'Shortened URL deleted successfully'}, HTTPStatus.OK