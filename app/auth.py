import re
import json
import base64
import hmac
import secrets
from flask import Blueprint, request

from .db import (
    add_user, search_user,
    change_password, delete_user,
    get_all_users
)


bp = Blueprint('auth', __name__, url_prefix='/api')

private_key = secrets.token_bytes()


def base64UrlEncode(data: dict):
    json_str = json.dumps(data)
    b = base64.b64encode(json_str.encode())
    return b.decode()


def authenticate_token(token: str):
    pattern = re.compile('^[a-zA-Z0-9=+/]+\.[a-zA-Z0-9=+/]+\.[a-zA-Z0-9=+/]+$')
    if pattern.match(token):
        [header, payload, signature] = token.split('.')
        signature2 = base64.b64encode(
            hmac.digest(private_key,
                        (header+'.'+payload).encode(),
                        'sha256')).decode()
        return signature == signature2
    else:
        return False


def get_user_from_token(token: str):
    pattern = re.compile('^[a-zA-Z0-9=+/]+\.[a-zA-Z0-9=+/]+\.[a-zA-Z0-9=+/]+$')
    if pattern.match(token):
        [header, payload, signature] = token.split('.')
        payload_str = base64.b64decode(payload).decode()
        payload_json = json.loads(payload_str)
        if 'user' in payload_json:
            return payload_json['user']
        else:
            return None
    else:
        return None


def generate_token(username: str):
    header = {'alg': 'HS256', 'typ': 'jwt'}
    payload = {'user': username}
    base64Str_h_p = base64UrlEncode(header)+'.'+base64UrlEncode(payload)

    signature = base64.b64encode(
        hmac.digest(private_key, base64Str_h_p.encode(), 'sha256')).decode()
    return base64Str_h_p+'.'+signature


@bp.route('/login', methods=['POST'])
def check_user():
    username = request.json['user']
    pwdHA = request.json['passwordHA']
    res = search_user(username)
    if res is not None:
        if res['password_ha'] == pwdHA:
            token = generate_token(username)
            return json.dumps({"result": 'Accept', 'token': token})
        else:
            return json.dumps(
                {"result": 'Deny', 'message': 'the password is not correct.'})
    else:
        return json.dumps(
            {"result": 'Deny', 'message': 'the username is not existed.'})


@bp.route('/change-password', methods=['POST'])
def change_user_password():
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.replace('Bearer ', '', 1)
        if authenticate_token(token):
            user = get_user_from_token(token)
            username = request.json['user']
            pwdHA = request.json['passwordHA']
            if user == username or user == 'admin':
                res = search_user(username)
                if res is not None:
                    change_password(username, pwdHA)
                    return json.dumps(
                        {"result": 'success'})
                else:
                    return json.dumps(
                        {"result": 'failed',
                         "message": 'This user is not existed.'})

    return "Unauthorized", 401


@bp.route('/add-user', methods=['POST'])
def create_user():
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.replace('Bearer ', '', 1)
        if authenticate_token(token):
            user = get_user_from_token(token)
            if user == 'admin':
                username = request.json['user']
                pwdHA = request.json['passwordHA']
                res = search_user(username)
                if res is None:
                    add_user(username, pwdHA)
                    return json.dumps(
                        {"result": 'success'})
                else:
                    return json.dumps(
                        {"result": 'failed',
                         "message": 'This user is already existed.'})
            else:
                return json.dumps(
                    {"result": 'failed',
                     "message": 'You are not \'admin\'.'})

    return "Unauthorized", 401


@bp.route('/delete-user', methods=['POST'])
def close_account():
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.replace('Bearer ', '', 1)
        if authenticate_token(token):
            user = get_user_from_token(token)
            username = request.json['user']
            if user == username or user == 'admin':
                if username == 'admin':
                    return json.dumps(
                        {"result": 'failed',
                         "message": '\'admin\' cannot be deleted.'})
                res = search_user(username)
                if res is not None:
                    delete_user(username)
                    return json.dumps(
                        {"result": 'success'})
                else:
                    return json.dumps(
                        {"result": 'failed',
                         "message": 'This user is not existed.'})

    return "Unauthorized", 401


@bp.route('/allusers', methods=['GET'])
def get_users():
    auth = request.headers.get('Authorization')
    if auth:
        token = auth.replace('Bearer ', '', 1)
        if authenticate_token(token):
            user = get_user_from_token(token)
            if user == 'admin':
                res = get_all_users()
                users = list(map(lambda row: row['username'], res))
                users = list(filter(lambda u: u != 'admin', users))
                return json.dumps(
                    {"result": 'success',
                     "allusers": users})
            else:
                return json.dumps(
                    {"result": 'failed',
                     "message": 'You are not \'admin\'.'})

    return "Unauthorized", 401
