from flask_login import login_required, current_user

from forms import MessageForm, IssueForm
from fuction_app import get_demande_by_id, get_messages_by_demande_id, add_gitlab_issue, get_milestones_by_app_id, \
    save_attachments, check_user_app_access
from flask import render_template, Blueprint, flash, render_template_string, request, jsonify, \
    redirect, url_for, current_app

from mail import mail_new_message
import gitlab
from sqlalchemy import desc
from models import Messages, Demandes, Statuts, DemandeIssue, Issues, Milestones, Labels
from setup import db, log, csrf
from constants import ACCES_REFUSE

messages_routes = Blueprint('messages_routes', __name__)


@messages_routes.route('/<demande_id>/messages', methods=['GET', 'POST'])
@login_required
def messages_list(demande_id):
    messages = get_messages_by_demande_id(demande_id)
    demande = get_demande_by_id(demande_id)

    if not demande or not check_user_app_access(current_user, demande.app_id):
        flash("Accès refusé à cette demande.", "danger")
        return redirect(url_for('app_routes.index'))

    statuts = db.session.query(Statuts).all()
    issues = db.session.query(Issues).filter_by(app_id=demande.app_id).filter_by(is_closed=False).filter_by(
        is_deleted=False).order_by(desc(Issues.git_id)).all()
    message_form = MessageForm()

    issue_form = IssueForm()

    if request.method == 'POST':
        # Ajout de l'issue dans GitLab
        try:
            issue_id = add_gitlab_issue(demande.app_id, issue_form.title.data, issue_form.description.data,
                                        issue_form.milestone_id.data, issue_form.label_ids.data)

            if issue_id:
                demande.statut_id = db.session.query(Statuts).filter_by(nom="Transformé en Issue").first().statut_id
                # Ajout du lien Demande / Issue
                demande_issue = DemandeIssue(demande_id=demande_id, issue_id=issue_id)
                db.session.add(demande_issue)
                db.session.commit()
                flash('Issue ajouté avec succès !', 'success')
            else:
                flash("Erreur interne lors de la création de l'issue.", "danger")

        except gitlab.exceptions.GitlabAuthenticationError:
            flash(
                f"Erreur d'authentification GitLab pour l'application {demande.app.acronyme}. Veuillez vérifier le token dans l'administration.",
                "danger")
        except Exception as e:
            flash(f"Erreur lors de la création de l'issue GitLab : {str(e)}", "danger")

        return redirect('/' + str(demande.demande_id) + '/messages')

    milestones = get_milestones_by_app_id(app_id=demande.app_id)
    labels = db.session.query(Labels).filter_by(app_id=demande.app_id).filter_by(is_deleted=False).all()

    # Remplit les choix pour les champs
    issue_form.title.data = demande.title
    issue_form.description.data = demande.description + "\n\nLien vers la demande sur Goupil : https://" + current_app.config['FLASK_FQDN'] + "/" + demande_id + "/messages"
    issue_form.milestone_id.choices = [(0, "Aucune")] + [(m.git_id, m.title) for m in milestones]
    issue_form.label_ids.choices = [(l.git_id, l.title) for l in labels]

    return render_template('messages/list.html', messages=messages, demande=demande, form=message_form, statuts=statuts,
                           issues=issues, issue_form=issue_form)


@messages_routes.route('/add_message', methods=['POST'])
@login_required
def add_message():
    form = MessageForm()
    # log.debug(form.data)
    if form.validate_on_submit():
        demande = db.session.query(Demandes).get(form.demande_id.data)
        if not demande or not check_user_app_access(current_user, demande.app_id):
            return ACCES_REFUSE, 403

        # Crée un nouveau message
        new_message = Messages(
            content=form.content.data,
            demande_id=form.demande_id.data,
            user_id=current_user.user_id
        )
        db.session.add(new_message)
        db.session.commit()

        attachments_list = request.files.getlist('attachments')
        if attachments_list:
            save_attachments(attachments_list, message_id=new_message.message_id)
            db.session.refresh(new_message)

        mail_new_message(new_message)

        # Rend le HTML du nouveau message pour HTMX
        return render_template_string('''
                    <div id="toast-zone" hx-swap-oob="beforeend">
                        <div id="toast-msg" class="flash-message success" 
                             hx-on:load="setTimeout(() => { this.style.opacity=0; this.style.transform='translateX(20px)'; setTimeout(()=>this.remove(), 500) }, 2000)">
                            Message ajouté avec succès !
                            <button onclick="this.parentElement.remove()" class="close-btn">&times;</button>
                        </div>
                    </div>
                    <div class="message {% if new_message.user.user_app|selectattr(\'app_id\', \'equalto\', new_message.demande.app_id)|selectattr(\'is_dev\', \'equalto\', True)|list %}message-dev{% else %}message-user{% endif %}">
                        <p>{{ new_message.content | replace(\'\\n\', \'<br>\') | safe }}</p>
                        {% if new_message.pieces_jointes %}
                            <div class="message-attachments">
                                {% for pj in new_message.pieces_jointes %}
                                     <a href="{{ url_for(\'app_routes.serve_upload\', filename=pj.filepath) }}" target="_blank" class="attachment-link message-attachment-link">
                                        <i class="fa-solid fa-paperclip"></i> {{ pj.filename }}
                                     </a>
                                {% endfor %}
                            </div>
                        {% endif %}
                        <small>
                            {{ new_message.user.username }} • {{ new_message.created_at.strftime("%H:%M - %d/%m/%y") }}
                        </small>
                    </div>
                    <script>setTimeout(function(){
                        var t=document.getElementById(\'toast-msg\');
                        if(t){t.style.transition=\'all 0.4s ease\';t.style.opacity=\'0\';t.style.transform=\'translateX(120%)\';setTimeout(function(){if(t.parentNode)t.remove();},400);}
                    },2500);</script>
                ''', new_message=new_message)

    # En cas d'erreur, retourne les erreurs pour HTMX
    return render_template_string('''
        <div class="error">
            {% for field, errors in form.errors.items() %}
                {% for error in errors %}
                    <span class="text-danger">{{ error }}</span><br>
                {% endfor %}
            {% endfor %}
        </div>
    ''', form=form), 400


@messages_routes.route('/demandes/<int:demande_id>/statut', methods=['PUT'])
@csrf.exempt
def update_demande_statut(demande_id):
    # Récupère le nouveau statut_id depuis la requête
    statut_id = request.form.get('statut_id', type=int)
    statuts = db.session.query(Statuts).all()

    if not statut_id:
        return jsonify({'error': 'statut_id manquant'}), 400

    # Met à jour la demande en base de données
    demande = db.session.query(Demandes).filter_by(demande_id=demande_id).first()
    if not demande or not check_user_app_access(current_user, demande.app_id):
        return ACCES_REFUSE, 403

    demande.statut_id = statut_id
    db.session.commit()

    # Retourne le nouveau statut pour mise à jour côté client
    return render_template_string('''
        <div
            hx-target="this"
            hx-swap="outerHTML"
        >
            <form
                hx-put="{{ url_for('messages_routes.update_demande_statut', demande_id=demande.demande_id) }}"
                hx-trigger="change"
                hx-include="[name='statut_id']"
            >
                <select
                    name="statut_id"
                    class="form-select"
                >
                    {% for statut in statuts %}
                        <option
                            value="{{ statut.statut_id }}"
                            {% if statut.statut_id == demande.statut_id %}selected{% endif %}
                        >
                            {{ statut.nom }}
                        </option>
                    {% endfor %}
                </select>
            </form>
        </div>
    ''', demande=demande, statuts=statuts)


@messages_routes.route('/demandes/<int:demande_id>/issue', methods=['PUT'])
@csrf.exempt
def update_demande_issue(demande_id):
    # Récupère le nouveau statut_id depuis la requête
    issue_id = request.form.get('issue_id', type=int)

    demande_id_int = int(demande_id)
    demande = db.session.query(Demandes).get(demande_id_int)
    if not demande or not check_user_app_access(current_user, demande.app_id):
        return ACCES_REFUSE, 403

    demande_issue = db.session.query(DemandeIssue).filter_by(demande_id=demande_id).first()
    if issue_id != 0:
        if demande_issue:
            demande_issue.issue_id = issue_id
        else:
            demande_issue = DemandeIssue(demande_id=demande_id, issue_id=issue_id)
            db.session.add(demande_issue)
        db.session.commit()
    else:
        if demande_issue:
            db.session.delete(demande_issue)
            db.session.commit()

    demande = get_demande_by_id(demande_id)
    issues = db.session.query(Issues).filter_by(app_id=demande.app_id).filter_by(is_closed=False).filter_by(
        is_deleted=False).order_by(desc(Issues.git_id)).all()
    # Retourne le nouveau statut pour mise à jour côté client
    return render_template_string('''
        <div
            hx-target="this"
            hx-swap="outerHTML"
        >
            <form
                hx-put="{{ url_for('messages_routes.update_demande_issue', demande_id=demande.demande_id) }}"
                hx-trigger="change"
                hx-include="[name='issue_id']"
            >
                <select
                    name="issue_id"
                    class="form-select"
                >
                    <option value="0" {% if not demande.demande_issue %} selected {% endif %}> Aucune Issue Associé </option>
                    {% for issue in issues %}
                        <option
                                value="{{ issue.issue_id }}"
                                {% if issue.demande_issue == demande.demande_issue and demande.demande_issue %}selected{% endif %}
                        >
                            #{{ issue.git_id }} - {{ issue.title }}
                        </option>
                    {% endfor %}
                </select>
            </form>
        </div>
    ''', demande=demande, issues=issues)
