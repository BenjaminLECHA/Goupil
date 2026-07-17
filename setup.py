import logging

from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from flask_dropzone import Dropzone

# Connexion à la base de donnés
db = SQLAlchemy()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

csrf = CSRFProtect()

login_manager = LoginManager()
dropzone = Dropzone()

mail = Mail()