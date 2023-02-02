from flask import Blueprint, request

bp = Blueprint('auth', __name__, url_prefix='/api')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

    return "ok"
