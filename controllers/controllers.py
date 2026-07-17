from flask_login import login_required, login_user, logout_user, current_user
import datetime

from forms import LoginForm, DemandeForm
from fuction_app import get_app_list, get_issues_by_app_id, get_app_name_by_id, get_demandes_by_app_id, \
    check_user_app_access, get_milestones_by_app_id, issue_matches_search, save_attachments
from flask import render_template, Blueprint, render_template_string, request, redirect, url_for, flash, \
    send_from_directory, current_app

from models import Users, Demandes, Statuts, Labels, PiecesJointes, CategorieDemande
from setup import db, log
from mail import mail_new_demand_to_dev
from constants import INDEX_ROUTE, ACCES_REFUSE

app_routes = Blueprint('app_routes', __name__)


@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data
        password = form.password.data
        user = db.session.query(Users).filter_by(email=email).first()
        if user:
            if user.check_password(password):
                user.last_login = datetime.datetime.now()
                db.session.commit()
                login_user(user)
                return redirect(url_for(INDEX_ROUTE))
            else:
                flash("Mot de passe incorrect.", "danger")
        else:
            flash("Identifiant inconnu.", "danger")

    return render_template('login.html', form=form)


@app_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app_routes.login'))


@app_routes.route('/')
@login_required
def index():
    app_user_list = current_user.get_app_list()
    app_list = get_app_list()
    return render_template('app/list.html', app_list=app_list, app_user_list=app_user_list)


@app_routes.route('/<int:app_id>', methods=['GET', 'POST'])
@login_required
def issues_list(app_id):
    form = DemandeForm()
    if request.method == 'POST':
        new_demande = Demandes(
            title=form.title.data,
            description=form.description.data,
            app_id=form.app_id.data,
            statut_id=1,
            user_id=current_user.user_id,
            categorie_id=form.categorie_id.data
        )
        db.session.add(new_demande)
        db.session.commit()

        attachments = request.files.getlist(form.attachments.name)
        if attachments:
            save_attachments(attachments, demande_id=new_demande.demande_id)
        mail_new_demand_to_dev(new_demande)
        flash('Demande ajouté avec succès !', 'success')
        return redirect('/' + str(app_id))
    if not check_user_app_access(current_user, app_id):
        return redirect(url_for(INDEX_ROUTE))
    app_name = get_app_name_by_id(app_id)
    statuts = db.session.query(Statuts).all()
    categories = db.session.query(CategorieDemande).all()
    form.categorie_id.choices = [(c.categorie_id, c.nom) for c in categories]
    users = db.session.query(Users).join(Demandes).filter(Demandes.app_id == app_id).distinct().all()
    labels = db.session.query(Labels).filter_by(app_id=app_id).filter_by(is_deleted=False).all()
    return render_template('issues/list.html', app_name=app_name, app_id=app_id, form=form, statuts=statuts,
                           users=users, labels=labels, categories=categories)


@app_routes.route('/<app_id>/issues/partial')
@login_required
def get_issues(app_id):
    if not check_user_app_access(current_user, int(app_id)):
        return redirect(url_for(INDEX_ROUTE))

    state = request.args.get('state')
    label_id = request.args.get('label_id', type=int)

    milestones = get_milestones_by_app_id(app_id)
    issues = get_issues_by_app_id(app_id, is_closed=state, label_id=label_id)

    response = render_template('partials/issues_list.html', milestones=milestones, issues=issues)
    response += render_template_string('''
        <span id="current-title" hx-swap-oob="true">Issues</span>
    ''')
    return response


@app_routes.route('/<app_id>/demandes/partial')
@login_required
def get_demandes(app_id):
    if not check_user_app_access(current_user, int(app_id)):
        return redirect(url_for(INDEX_ROUTE))
    statut_id = request.args.get('statut_id', type=int)
    user_id = request.args.get('user_id', type=int)
    demandes = get_demandes_by_app_id(app_id, statut_id, user_id)
    mes_demandes_ouvertes = []
    autres_demandes_ouvertes = []
    mes_demandes_fermees = []
    autres_demandes_fermees = []
    for demande in demandes:
        if demande.user_id == current_user.user_id:
            if demande.statut.nom == 'Demande fermé':
                mes_demandes_fermees.append(demande)
            else:
                mes_demandes_ouvertes.append(demande)
        else:
            if demande.statut.nom == 'Demande fermé':
                autres_demandes_fermees.append(demande)
            else:
                autres_demandes_ouvertes.append(demande)
    response = render_template('partials/demandes_list.html',
                               mes_demandes_ouvertes=mes_demandes_ouvertes,
                               autres_demandes_ouvertes=autres_demandes_ouvertes,
                               mes_demandes_fermees=mes_demandes_fermees,
                               autres_demandes_fermees=autres_demandes_fermees)
    response += render_template_string('''
            <span id="current-title" hx-swap-oob="true">Demandes</span>
        ''')
    return response


@app_routes.route('/<app_id>/search/partial')
@login_required
def search(app_id):
    if not check_user_app_access(current_user, int(app_id)):
        return redirect(url_for(INDEX_ROUTE))

    search_query = request.args.get('q', '').strip().lower()
    log.debug(search_query)
    milestones = get_milestones_by_app_id(app_id)
    issues = get_issues_by_app_id(app_id)
    demandes = get_demandes_by_app_id(app_id)

    # Filtrer les milestones et issues en fonction de la recherche
    if search_query:
        issues = [i for i in issues if issue_matches_search(i, search_query)]
        demandes = [i for i in demandes if issue_matches_search(i, search_query)]

    response = render_template('partials/search_list.html', milestones=milestones, issues=issues, demandes=demandes)
    response += render_template_string('''
        <span id="current-title" hx-swap-oob="true">Recherche dans les demandes et issues</span>
    ''')
    return response


@app_routes.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    pj = db.session.query(PiecesJointes).filter_by(filepath=filename).first()
    if not pj:
        log.debug(f"Fichier non trouvé : {filename}")
        return "Fichier non trouvé", 404

    app_id = None
    if pj.demande:
        app_id = pj.demande.app_id
    elif pj.message and pj.message.demande:
        app_id = pj.message.demande.app_id

    if app_id and check_user_app_access(current_user, app_id):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

    log.warning(f"Tentative d'accès non autorisé au fichier {filename} par l'utilisateur {current_user.username}")
    return ACCES_REFUSE, 403


@app_routes.route('/dropzone_upload', methods=['POST'])
@login_required
def dropzone_upload():
    if 'file' in request.files:
        f = request.files.get('file')
        return "OK", 200
    return "No file", 400
