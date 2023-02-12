import os
import sqlite3
import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        url = os.path.join(current_app.instance_path,
                           current_app.config['DATABASE'])
        g.db = sqlite3.connect(
            url,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def search_user(username: str):
    db = get_db()
    res = db.execute(
        "SELECT password_ha FROM user WHERE username=?",
        (username,)
    )
    return res.fetchone()


def get_all_users():
    db = get_db()
    res = db.execute(
        "SELECT username FROM user"
    )
    return res.fetchall()


def change_password(username: str, pwd: str):
    db = get_db()
    db.execute(
        "UPDATE user SET password_ha=? WHERE username=?", (pwd, username)
    )
    db.commit()


def add_user(username: str, pwd: str):
    db = get_db()
    db.execute(
        "INSERT INTO user (username, password_ha) VALUES (?, ?)",
        (username, pwd)
    )
    db.commit()


def delete_user(username: str):
    db = get_db()
    db.execute(
        "DELETE FROM user WHERE username=?", (username,)
    )
    db.commit()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf-8'))


@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
