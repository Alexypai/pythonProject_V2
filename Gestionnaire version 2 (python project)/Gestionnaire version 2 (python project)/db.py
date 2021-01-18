'''This file will create the 
connection between our 
database and our programm'''

import sqlite3

import click
import os
from flask import current_app, g, request
from flask.cli import with_appcontext
from werkzeug.security import check_password_hash, generate_password_hash


# function called for get db
def get_cursor():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )

    return g.db.cursor()


# closing the db
def close_db(e=None):
    # We close the database when we finished gathering datas
    db = g.pop('db', None)

    if db is not None:
        db.close()


# Initialization of the db with BDD_python_project.sql and data.sql files
def init_db():
    db = get_cursor()

    # check if table is create
    with current_app.open_resource('BDD_python_project.sql') as f:
        db.executescript(f.read().decode('utf8'))

    #if they are no data in the db get it with data.sql (is use only if  they are no data in db file)
    db.execute('SELECT * FROM USERS')
    Users_Init = db.fetchall()
    if not Users_Init:
        with current_app.open_resource('data.sql') as f:
            db.executescript(f.read().decode('utf8'))


# test for Initialization of the db if we use the console
@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Base de données initialisée')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
