from flask_restx import Namespace, Resource, fields
from flask import redirect, request, jsonify, send_file, make_response, url_for, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.qrcode import Qrcode
from ..models.user import User
from ..models.analytics import Analytic
from ..models.shorturl import Shorturl
from ..utils import db
from urllib.parse import urlparse, urlunparse
from werkzeug.urls import url_parse, url_encode
from datetime import datetime
from ..config.config import cache, limiter
from http import HTTPStatus
import urllib.parse
import qrcode
import requests
import uuid
from io import BytesIO
import io
import base64

qrcode_namespace = Namespace('qrcode', description='QR Code Operations')

shortlink_model = qrcode_namespace.model(
    'Shorturl', {
        'short_url': fields.String(required=True, description='Short URL')
    }
)

qrcode_model = qrcode_namespace.model(
    'QRCode', {
        'id': fields.Integer(description='QR Code ID'),
        'short_url_id': fields.Integer(description='Short URL ID'),
        'download_link': fields.String(description='Download Link'),
        'short_url': fields.String(description='Short URL')
    }
)

@qrcode_namespace.route('/generate')
class QRCodeGenerator(Resource):
    @limiter.limit("10 per minute")
    @qrcode_namespace.expect(shortlink_model)
    @qrcode_namespace.produces(['image/png'])
    @qrcode_namespace.doc(
            description='Generate A QR-CODE FOR A SHORTENED URL'
    )
    @jwt_required()
    def post(self):
        """
        Generate QR Code for Short URL
        """
        current_user = User.query.filter_by(firstname=get_jwt_identity()).first()
        user_id = current_user.id

        data = qrcode_namespace.payload
        short_url = data.get('short_url')

        shortened_url = Shorturl.query.filter_by(short_url=short_url).first()
        if not shortened_url:
            return {'message': 'URL not found'}, 404

        if shortened_url.user_id != user_id:
            return {'message': 'URL not found'}, 404

        existing_qrcode = Qrcode.query.filter_by(
            short_url_id=shortened_url.id,
            user_id=user_id
        ).first()

        if existing_qrcode:
            return {'message': 'QR code already generated for the short URL by the current user'}, 400

        qr_data = shortened_url.long_url

        qr = qrcode.QRCode()
        qr.add_data(qr_data)
        qr.make(fit=True)
        pil_img = qr.make_image()

        img_io = BytesIO()
        pil_img.save(img_io, 'PNG')
        img_io.seek(0)
        img_bytes = img_io.getvalue()

        qrcode_entry = Qrcode(
            short_url_id=shortened_url.id,
            user_id=user_id,
            image=img_bytes,
            qr_identifier=str(uuid.uuid4()) 
        )
        db.session.add(qrcode_entry)
        db.session.commit()

        return send_file(BytesIO(qrcode_entry.image), mimetype='image/png')


@qrcode_namespace.route('/<string:short_url>')
class QRCodeImage(Resource):
    @qrcode_namespace.doc(
            description='Get A QR-Code For A Shortened URL',
            params={'short_url': 'Short URL'}
    )
    @cache.cached(timeout=60)
    @jwt_required()
    def get(self, short_url):
        """
        Get QR Code Image to DOWNLOAD by Short URL
        """
        
        current_user = User.query.filter_by(firstname=get_jwt_identity()).first()

        shortened_url = Shorturl.query.filter_by(short_url=short_url).first()
        if not shortened_url:
             return {'message': 'You do not have such Shortened URL saved'}, 404

        if shortened_url.user_id != current_user.id:
            return {'message': 'QrCode image not found'}, 404
        
        qrcode_entry = Qrcode.query.join(Shorturl).filter(Shorturl.short_url == short_url).first()

        if not qrcode_entry:
            return {'message': 'QR Code image not found'}, 404
        
        headers = {
            'Content-Disposition': 'attachment; filename=qrcode.png'
        }

        response = make_response(qrcode_entry.image)
        response.headers = headers
        response.mimetype = 'image/png'
        return response