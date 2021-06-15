from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
db = SQLAlchemy()
DB_Name = "database.db"


#UNTUK INISIAL APP
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_Name}'
    db.init_app(app)

    
    #MEMASUKAN BLUEPRINT
    from .view import views
    app.register_blueprint(views, url_prefix="/")

    #MEMBUAT DATABASE
    from .model import Users, Manga, Profiles, Chapter, ImageSet, Report
    create_database(app)

    app.jinja_env.filters['zip'] = zip

    #MEMBUAT LOGIN MANAGER
    login_manager = LoginManager()
    login_manager.login_view = 'views.auth'
    login_manager.init_app(app)

    #LOAD DATA USER
    @login_manager.user_loader
    def load_user(id):
        return Users.query.get(int(id))
    
    #MENGEMBALIKAN APP YANG SUDAH TERINISIAL
    return app

def create_database(app):
    if not path.exists('website/' + DB_Name):
        db.create_all(app=app)
        print('Database Created!')
