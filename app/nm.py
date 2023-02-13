import json
from flask import Blueprint, request
from .send_to_nm import requset_to_networkmanager


bp = Blueprint('networking', __name__, url_prefix='/api')


@bp.route('/allaps', methods=['GET'])
def get_all_aps():
    auth = request.headers.get('Authorization')
    data = {'request': 'getWifiAps'}
    response = requset_to_networkmanager(json.dumps(data))
    result = response.get(block=True, timeout=5)
    return str(result)
