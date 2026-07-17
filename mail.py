from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from setup import mail, db, log
from models import Users, UserApp, Messages


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            log.error(f"Erreur lors de l'envoi d'un email asynchrone ({msg.subject}) : {str(e)}")


def send_email(subject, recipients, template, **kwargs):
    """
    Envoie un email de manière asynchrone en utilisant un template Jinja2.

    :param subject: Sujet de l'email
    :param recipients: Liste des destinataires
    :param template: Nom du template Jinja2 (sans l'extension .html)
    :param kwargs: Variables à passer au template
    """
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    msg.html = render_template(f'{template}.html', **kwargs)
    msg.content_subtype = "html"

    Thread(target=send_async_email, args=(app, msg)).start()


def mail_new_message(message):
    demande = message.demande
    sender = message.user

    recipients = {}

    if demande.user and demande.user.email and demande.user_id != sender.user_id:
        recipients[demande.user.user_id] = demande.user

    devs = db.session.query(Users).join(UserApp).filter(
        UserApp.app_id == demande.app_id,
        UserApp.is_dev == True
    ).all()
    for d in devs:
        if d.email and d.user_id != sender.user_id:
            recipients[d.user_id] = d

    participants = db.session.query(Users).join(Messages).filter(
        Messages.demande_id == demande.demande_id
    ).all()
    for p in participants:
        if p.email and p.user_id != sender.user_id:
            recipients[p.user_id] = p

    for user_id, recipient in recipients.items():
        is_dev = any(ua.app_id == demande.app_id and ua.is_dev for ua in recipient.user_app)

        template = "mail/new_message_to_dev" if is_dev else "mail/new_message_to_user"
        subject = f"[GOUPIL] - Message à propos de la demande : {demande.title}"

        send_email(
            subject=subject,
            recipients=[recipient.email],
            template=template,
            demande=demande,
            message=message,
            recipient_name=recipient.username,
            app_name=f"{demande.app.acronyme} - Message"
        )


def mail_new_demand_to_dev(demande):
    devs = db.session.query(Users).join(UserApp).filter(
        UserApp.app_id == demande.app_id,
        UserApp.is_dev == True
    ).all()
    emails = [d.email for d in devs if d.email]
    if emails:
        send_email(
            subject=f"[GOUPIL] - Nouvelle demande : {demande.title}",
            recipients=emails,
            template="mail/new_demand_dev",
            demande=demande,
            app_name=f"{demande.app.acronyme} - Suivi de projet"
        )


def mail_token_error(app_obj):
    """
    Envoie un email à l'administration en cas d'erreur de token GitLab.
    """
    subject = f"[GOUPIL] - Erreur d'accès GitLab : {app_obj.acronyme}"
    send_email(
        subject=subject,
        recipients=[current_app.config['MAIL_DEFAULT_RECEIVER']],
        template="mail/token_error",
        app_acronyme=app_obj.acronyme,
        app_name="Goupil - Alerte Système"
    )