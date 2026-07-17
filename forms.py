from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField, StringField, PasswordField, SelectField, \
    SelectMultipleField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Email

LABEL_CONTENU_MESSAGE = 'Contenu du message'

class DemandeForm(FlaskForm):
    app_id = HiddenField('App ID')  # Pour stocker l'ID de l'app
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField(LABEL_CONTENU_MESSAGE, validators=[DataRequired()], render_kw={"rows": 4, "cols": 150, "placeholder": "Écrivez votre description ici..."})
    categorie_id = SelectField('Catégorie', coerce=int, validators=[DataRequired()])
    attachments = MultipleFileField('Pièces jointes', render_kw={'multiple': True})
    submit = SubmitField('Envoyer')

class IssueForm(FlaskForm):# Pour stocker l'ID de l'app
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField(LABEL_CONTENU_MESSAGE, validators=[DataRequired()], render_kw={"rows": 4, "cols": 150, "placeholder": "Écrivez votre description ici..."})
    milestone_id = SelectField('Milestone', coerce=int, validate_choice=False)
    label_ids = SelectMultipleField('Labels', coerce=int)
    submit = SubmitField('Envoyer')

class MessageForm(FlaskForm):
    demande_id = HiddenField('Demande ID')  # Pour stocker l'ID de l'issue
    content = TextAreaField(LABEL_CONTENU_MESSAGE, validators=[DataRequired()], render_kw={"rows": 4, "cols": 150, "placeholder": "Écrivez votre message ici..."})
    attachments = MultipleFileField('Pièces jointes', render_kw={'multiple': True})
    submit = SubmitField('Envoyer')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('', validators=[DataRequired()])
    submit = SubmitField('Envoyer')

class UserForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe')
    is_admin = BooleanField('Administrateur')
    submit = SubmitField('Enregistrer')

class UserResetPasswordForm(FlaskForm):
    password = PasswordField('Nouveau mot de passe', validators=[DataRequired()])
    submit = SubmitField('Réinitialiser')