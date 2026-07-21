import os
from flask import Flask, redirect, url_for, flash
from sqlalchemy import text
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user, login_required
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from wtforms import PasswordField
from apscheduler.schedulers.background import BackgroundScheduler

from controllers.controllers import app_routes
from controllers.gitlab import gitlab_routes
from controllers.messages import messages_routes
from fuction_app import update_gitlab_data, get_is_dev
from setup import db, csrf, login_manager, mail, dropzone, log
from models import Users, App, Demandes, Statuts, UserApp

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config.from_prefixed_env()

# Active la protection CSRF
csrf.init_app(app)

# Config des uploads modifié à la volé pour la création si nécessaire dans le conteneur
app.config['UPLOAD_FOLDER'] = (os.path.join(app.root_path, app.config['UPLOAD_FOLDER']))

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Config Dropzone
dropzone.init_app(app)

app.config['MAIL_DEBUG'] = app.config['MAIL_DEBUG'].lower() == 'true'
mail.init_app(app)

db.init_app(app)

# Config du login
login_manager.login_view = 'app_routes.login'
login_manager.init_app(app)

log.debug(app.config['MAIL_SERVER'])


@app.route('/health')
@csrf.exempt
def health():
    """
    Endpoint de healthcheck (utilisé par le HEALTHCHECK du Dockerfile).
    Vérifie la connexion à la base de données.
    """
    try:
        db.session.execute(text('SELECT 1'))
        return {"status": "ok", "database": "up"}, 200
    except Exception as e:
        log.error(f"Healthcheck DB failed: {e}")
        return {"status": "error", "database": "down"}, 503


# Ajout des routes
app.register_blueprint(app_routes)
app.register_blueprint(gitlab_routes)
app.register_blueprint(messages_routes)

app.add_template_global(get_is_dev, name='is_dev')
app.add_template_global(app.config["FQDN"], name='FQDN')


# Flask-Admin config
class MyAdminIndexView(AdminIndexView):
    def is_visible(self):
        return False

    @expose('/')
    def index(self):
        return redirect(url_for('users.index_view'))

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        flash('Accès réservé aux administrateurs.', 'warning')
        return redirect(url_for('app_routes.index'))


class AdminModelView(ModelView):
    can_view_details = True
    action_disallowed_list = ['delete']
    page_size = 1000
    extra_css = ['/static/css/admin_custom.css']

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)

    def inaccessible_callback(self, name, **kwargs):
        flash('Accès réservé aux administrateurs.', 'warning')
        return redirect(url_for('app_routes.index'))


class UserModelView(AdminModelView):
    can_delete = False
    column_list = ('username', 'email', 'is_admin', 'last_login', 'is_active')
    form_columns = ('username', 'email', 'is_admin', 'is_active', 'password')
    form_extra_fields = {
        'password': PasswordField('Mot de passe')
    }
    column_searchable_list = ['username', 'email']

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)


class ProjectModelView(AdminModelView):
    can_delete = False
    column_exclude_list = ['private_token', 'demandes', 'issues', 'labels', 'milestones', 'user_app']
    column_searchable_list = ['name', 'acronyme']
    column_details_list = ['app_id', 'name', 'acronyme', 'git_id', 'git_url', 'private_token', 'description']
    form_columns = ('name', 'acronyme', 'git_id', 'git_url', 'private_token', 'description')


class UserAppModelView(AdminModelView):
    column_list = ('user', 'app', 'is_dev')
    column_labels = {
        'user': 'Utilisateur',
        'app': 'Projet',
        'is_dev': 'Développeur'
    }
    column_searchable_list = ('user.username', 'app.acronyme', 'app.name')
    column_sortable_list = (
        ('user', 'user.username'),
        ('app', 'app.acronyme'),
        'is_dev'
    )

    form_ajax_refs = {
        'user': {
            'fields': (Users.username, Users.email)
        },
        'app': {
            'fields': (App.name, App.acronyme)
        }
    }


class DemandesModelView(AdminModelView):
    column_searchable_list = ['title', 'description']


admin = Admin(app, name='Goupil Admin', theme=Bootstrap4Theme(), index_view=MyAdminIndexView())
admin.add_view(UserModelView(Users, db.session, name="Utilisateurs", endpoint="users"))
admin.add_view(ProjectModelView(App, db.session, name="Projets", endpoint="projects"))
admin.add_view(UserAppModelView(UserApp, db.session, name="Attributions Projets", endpoint="user_app"))
admin.add_view(DemandesModelView(Demandes, db.session, name="Demandes", endpoint="demandes"))
admin.add_link(MenuLink(name='Retour au site', url='/'))

app.add_template_global(get_is_dev, name='is_dev')
app.add_template_global(app.config["FQDN"], name='FQDN')


def update_data():
    with app.app_context():
        update_gitlab_data()


if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_data, 'interval', hours=6)
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)