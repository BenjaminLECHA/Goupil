import os
import datetime
from datetime import date
from flask import current_app
from werkzeug.utils import secure_filename

import gitlab
from sqlalchemy import case, func, extract, desc

from setup import db, log, login_manager
from models import App, Issues, Messages, Milestones, Labels, LabelIssue, MillestoneIssue, Demandes, Users, UserApp, \
    PiecesJointes
from mail import mail_token_error


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(int(user_id))


def get_is_dev(app_id, user_id):
    user = db.session.query(Users).get(int(user_id))
    if user and user.is_admin:
        return True
    user_app = db.session.query(UserApp).filter_by(user_id=user_id, app_id=app_id).first()
    return user_app.is_dev if user_app else False


def check_user_app_access(user, app_id):
    return app_id in user.get_app_list()


def get_private_token_by_git_id(git_id):
    app = db.session.query(App).filter_by(git_id=git_id).first()
    return app.private_token


def get_app_id_by_git_id(git_id):
    app = db.session.query(App).filter_by(git_id=git_id).first()
    return app.app_id


def get_app_by_app_id(app_id):
    app = db.session.query(App).filter_by(app_id=app_id).first()
    return app


def get_app_list():
    app_list = db.session.query(App).all()
    return app_list


def get_app_name_by_id(app_id):
    app = db.session.query(App).filter_by(app_id=app_id).first()
    return app.acronyme


def get_issue_by_id(issue_id):
    issue = db.session.query(Issues).filter_by(issue_id=issue_id).first()
    return issue


def get_demande_by_id(demande_id):
    demande = db.session.query(Demandes).filter_by(demande_id=demande_id).first()
    return demande


def get_issues_by_app_id(app_id, is_closed=None, label_id=None):
    query = db.session.query(Issues).filter_by(app_id=app_id).filter_by(is_deleted=False)

    if is_closed is not None:
        if isinstance(is_closed, str):
            if is_closed == "open":
                query = query.filter_by(is_closed=False)
            elif is_closed == "closed":
                query = query.filter_by(is_closed=True)
        elif isinstance(is_closed, bool):
            query = query.filter_by(is_closed=is_closed)

    if label_id and int(label_id) != 0:
        query = query.join(LabelIssue).filter(LabelIssue.label_id == label_id)

    issues = query.all()
    return issues


def get_demandes_by_app_id(app_id, statut_id=None, user_id=None):
    query = db.session.query(Demandes).filter_by(app_id=app_id)
    if statut_id and int(statut_id) != 0:
        query = query.filter_by(statut_id=statut_id)
    if user_id and int(user_id) != 0:
        query = query.filter_by(user_id=user_id)
    demandes = query.order_by(desc(Demandes.created_at)).all()
    return demandes


def get_issue_by_git_id(git_id, app_id):
    issues = db.session.query(Issues).filter_by(git_id=git_id, app_id=app_id).first()
    return issues


def add_issue(data, app_id):
    new_issue = Issues(
        title=data['title'],
        description=data['description'],
        git_id=data['iid'],
        is_closed=data['state'] == 'closed',
        app_id=app_id
    )
    db.session.add(new_issue)
    db.session.commit()

    return new_issue


def get_messages_by_demande_id(demande_id):
    messages = db.session.query(Messages).filter_by(demande_id=demande_id).all()
    return messages


def get_label_by_git_id(git_id, app_id):
    label = db.session.query(Labels).filter_by(git_id=git_id, app_id=app_id).first()
    return label


def add_label(data, app_id):
    new_label = Labels(
        title=data['title'],
        description=data['description'],
        app_id=app_id,
        git_id=data['id'],
        color=data['color']
    )
    db.session.add(new_label)
    db.session.commit()

    return new_label


def get_link_label_issue(label_id, issue_id):
    label_issue = db.session.query(LabelIssue).filter_by(label_id=label_id, issue_id=issue_id).first()
    return label_issue


def rm_link_label_issue(issue_id):
    db.session.query(LabelIssue).filter_by(issue_id=issue_id).delete()
    db.session.commit()


def add_link_label_issue(label_id, issue_id):
    label_issue = LabelIssue(
        label_id=label_id,
        issue_id=issue_id,
    )
    db.session.add(label_issue)
    db.session.commit()


def get_milestone_by_git_id(git_id, app_id):
    milestone = db.session.query(Milestones).filter_by(git_id=git_id, app_id=app_id).first()
    return milestone


def get_milestones_by_app_id(app_id):
    today = date.today()
    query = db.session.query(Milestones).filter_by(app_id=app_id).filter_by(is_deleted=False).order_by(
        # 1. Priorité absolue : non supprimés et non fermés
        case(
            (
                (Milestones.is_closed == False) &
                (Milestones.is_deleted == False),
                0  # Priorité maximale
            ),
            (
                (Milestones.is_closed == True) &
                (Milestones.is_deleted == False),
                1  # Priorité moyenne
            ),
            else_=None  # Priorité minimale (supprimés)
        ).asc(),

        # 2. Tri par date pour les non fermés/non supprimés
        case(
            (
                (Milestones.is_closed == False) &
                (Milestones.is_deleted == False),
                case(
                    (
                        Milestones.start_date.isnot(None),
                        func.abs(Milestones.start_date - today)
                    ),
                    else_=None
                )
            ),
            else_=None
        ).asc(),
    )
    milestones = query.all()
    return milestones


def add_milestone(data, app_id):
    new_milestone = Milestones(
        title=data['title'],
        description=data['description'],
        start_date=data['start_date'],
        due_date=data['due_date'],
        is_closed=data['state'] == 'closed',
        git_id=data['id'],
        app_id=app_id
    )
    db.session.add(new_milestone)
    db.session.commit()


def get_link_milestone_issue_by_issue(issue_id):
    milestone_issue = db.session.query(MillestoneIssue).filter_by(issue_id=issue_id).first()
    return milestone_issue


def get_link_milestone_issue_by_milestone(milestone_id):
    milestone_issue = db.session.query(MillestoneIssue).filter_by(milestone_id=milestone_id).first()
    return milestone_issue


def rm_link_milestone_issue(issue_id):
    db.session.query(MillestoneIssue).filter_by(issue_id=issue_id).delete()
    db.session.commit()


def add_link_milestone_issue(milestone_id, issue_id):
    milestone_issue = MillestoneIssue(
        milestone_id=milestone_id,
        issue_id=issue_id
    )

    db.session.add(milestone_issue)
    db.session.commit()


def update_link_issue_miilestone(milestone_id, issue):
    """
    Met à jour ou supprime le lien entre une issue et un milestone.
    """
    db.session.query(MillestoneIssue).filter_by(issue_id=issue.issue_id).delete()

    if milestone_id:
        mi = MillestoneIssue(milestone_id=milestone_id, issue_id=issue.issue_id)
        db.session.add(mi)

    db.session.commit()


def add_gitlab_issue(app_id, titre, description, millestone_id, labels_ids):
    app = get_app_by_app_id(app_id)
    gl = gitlab.Gitlab(app.git_url, private_token=app.private_token)
    projet = gl.projects.get(app.git_id)

    issue_data = {
        'title': titre,
        'description': description,
    }

    issue = projet.issues.create(issue_data)

    issue.labels = []
    for label_id in labels_ids:
        label = get_label_by_git_id(label_id, app_id)
        if label:
            issue.labels.append(label.title)

    issue.milestone_id = millestone_id
    issue.save()

    local_issue = db.session.query(Issues).filter_by(git_id=issue.iid, app_id=app_id).first()

    if not local_issue:
        local_issue = Issues(
            title=titre,
            description=description,
            git_id=issue.iid,
            app_id=app_id,
            web_url=getattr(issue, 'web_url', None)
        )

        db.session.add(local_issue)
        db.session.commit()

    link_milestone_issue = get_link_milestone_issue_by_issue(local_issue.issue_id)
    if link_milestone_issue is None:
        ms = db.session.query(Milestones).filter_by(git_id=millestone_id, app_id=app_id).first()
        if ms:
            link_milestone_issue = MillestoneIssue(
                milestone_id=ms.milestone_id,
                issue_id=local_issue.issue_id,
            )
            db.session.add(link_milestone_issue)
            db.session.commit()

    return local_issue.issue_id


def _sync_labels(projet, app_id):
    # On inclut les labels des groupes parents pour une vision complète
    labels = projet.labels.list(all=True, include_ancestor_groups=True)
    gitlab_labels_ids = [label.id for label in labels]

    for label in labels:
        check_label = get_label_by_git_id(label.id, app_id)
        if check_label:
            check_label.title = label.name
            check_label.description = label.description
            check_label.color = label.color
            check_label.is_deleted = False
        else:
            new_label = Labels(
                title=label.name,
                description=label.description,
                git_id=label.id,
                color=label.color,
                app_id=app_id
            )
            db.session.add(new_label)
    db.session.commit()

    # Mark deleted labels
    db.session.query(Labels).filter(
        Labels.app_id == app_id,
        Labels.git_id.notin_(gitlab_labels_ids)
    ).update({Labels.is_deleted: True}, synchronize_session=False)
    db.session.commit()
    return labels


def _sync_milestones(projet, app_id):
    # On récupère tous les milestones (actifs et fermés), incluant ceux des groupes parents
    milestones = projet.milestones.list(all=True, state='all', include_parent_milestones=True)
    gitlab_milestone_ids = [milestone.id for milestone in milestones]

    for milestone in milestones:
        check_milestone = get_milestone_by_git_id(milestone.id, app_id)
        if check_milestone:
            check_milestone.title = milestone.title
            check_milestone.description = milestone.description
            check_milestone.start_date = milestone.start_date
            check_milestone.due_date = milestone.due_date
            check_milestone.is_closed = milestone.state == 'closed'
            check_milestone.is_deleted = False
        else:
            new_milestone = Milestones(
                title=milestone.title,
                description=milestone.description,
                start_date=milestone.start_date,
                due_date=milestone.due_date,
                is_closed=milestone.state == 'closed',
                git_id=milestone.id,
                app_id=app_id
            )
            db.session.add(new_milestone)
    db.session.commit()

    # Mark deleted milestones
    db.session.query(Milestones).filter(
        Milestones.app_id == app_id,
        Milestones.git_id.notin_(gitlab_milestone_ids)
    ).update({Milestones.is_deleted: True}, synchronize_session=False)
    db.session.commit()


def _upsert_single_issue(issue, app_id, labels):
    check_issue = get_issue_by_git_id(issue.iid, app_id)

    if not check_issue:
        check_issue = db.session.query(Issues).filter_by(git_id=issue.id, app_id=app_id).first()
        if check_issue:
            check_issue.git_id = issue.iid
            db.session.commit()

    issue_labels_details = [label for label in labels if label.name in issue.labels]

    milestone_id = None
    if issue.milestone:
        # On essaie de récupérer l'ID de la milestone de manière robuste (dict ou objet)
        git_milestone_id = issue.milestone.get('id') if isinstance(issue.milestone, dict) else getattr(issue.milestone,
                                                                                                       'id', None)
        if git_milestone_id:
            milestone = get_milestone_by_git_id(git_milestone_id, app_id)
            if milestone:
                milestone_id = milestone.milestone_id

    if not check_issue:
        check_issue = Issues(
            title=issue.title,
            description=issue.description,
            git_id=issue.iid,
            is_closed=issue.state == 'closed',
            app_id=app_id,
            is_deleted=False,
            web_url=getattr(issue, 'web_url', None)
        )
        db.session.add(check_issue)
    else:
        check_issue.title = issue.title
        check_issue.description = issue.description
        state_str = str(issue.state).lower()
        check_issue.is_closed = (state_str == 'closed')
        check_issue.is_deleted = False
        check_issue.web_url = getattr(issue, 'web_url', None)

    db.session.commit()

    rm_link_label_issue(check_issue.issue_id)
    for label_data in issue_labels_details:
        label_obj = get_label_by_git_id(label_data.id, app_id)
        if label_obj:
            add_link_label_issue(label_obj.label_id, check_issue.issue_id)

    update_link_issue_miilestone(milestone_id, check_issue)


def _sync_issues(projet, app_id, labels):
    # On récupère toutes les issues (ouvertes et fermées)
    issues = projet.issues.list(get_all=True, state='all')
    gitlab_issue_ids = [issue.iid for issue in issues]

    for issue in issues:
        _upsert_single_issue(issue, app_id, labels)

    # Mark deleted issues
    db.session.query(Issues).filter(
        Issues.app_id == app_id,
        Issues.git_id.notin_(gitlab_issue_ids)
    ).update({Issues.is_deleted: True}, synchronize_session=False)
    db.session.commit()


def update_gitlab_data():
    log.debug("--- CRON start ---")
    for app in get_app_list():
        if not app.private_token or not app.git_url:
            log.warning(f"Saut de la synchro pour {app.acronyme}: URL ou Token manquant")
            continue

        gl = gitlab.Gitlab(app.git_url, private_token=app.private_token.strip())
        try:
            projet = gl.projects.get(app.git_id)
            labels = _sync_labels(projet, app.app_id)
            _sync_milestones(projet, app.app_id)
            _sync_issues(projet, app.app_id, labels)
        except gitlab.exceptions.GitlabAuthenticationError:
            log.error(f"Synchro échouée pour {app.acronyme}: Token invalide (401)")
            mail_token_error(app)
            continue

        except Exception as e:
            log.error(f"Synchro échouée pour {app.acronyme}: {str(e)}")
            continue


def issue_matches_search(issue, search_query):
    title_match = search_query in issue.title.lower()
    description = issue.description or ""
    description_match = search_query in description.lower()
    categorie_match = False
    if hasattr(issue, 'categorie') and issue.categorie:
        categorie_match = search_query in issue.categorie.nom.lower()
    return title_match or description_match or categorie_match


ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp',
    'pdf',
    'xlsx', 'xls', 'csv', 'ods',
    'docx', 'doc', 'odt',
    'txt'
}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _get_demande_path_info(demande_id):
    demande = db.session.query(Demandes).get(demande_id)
    if not demande:
        return "demandes", f"d_{demande_id}"

    u_id = demande.user_id or 0
    a_id = demande.app_id or 0
    app_acronyme = demande.app.acronyme if (demande.app and demande.app.acronyme) else "unknown"
    return os.path.join("demandes", app_acronyme), f"{demande_id}_{u_id}_{a_id}"


def _get_message_path_info(message_id):
    message = db.session.query(Messages).get(message_id)
    if not message:
        return "messages", f"m_{message_id}"

    u_id = message.user_id or 0
    d_id = message.demande_id or 0
    app_obj = message.demande.app if (message.demande and message.demande.app) else None
    app_acronyme = app_obj.acronyme if app_obj else "unknown"
    return os.path.join("messages", app_acronyme), f"{message_id}_{d_id}_{u_id}"


def _get_attachment_path_info(demande_id, message_id):
    if demande_id:
        return _get_demande_path_info(demande_id)
    if message_id:
        return _get_message_path_info(message_id)
    return "", ""


def _save_single_file(file, i, prefix, subfolder, upload_folder, demande_id, message_id, num_files):
    if not (file and hasattr(file, 'filename') and file.filename and allowed_file(file.filename)):
        return

    sec_filename = secure_filename(file.filename)
    ext = sec_filename.rsplit('.', 1)[1] if '.' in sec_filename else ""

    fn = f"{prefix}_{i}" if num_files > 1 else prefix
    unique_filename = f"{fn}.{ext}" if ext else fn

    rel_filepath = os.path.join(subfolder, unique_filename) if subfolder else unique_filename
    file.save(os.path.join(upload_folder, rel_filepath))

    new_pj = PiecesJointes(
        filename=sec_filename, filepath=rel_filepath,
        demande_id=demande_id, message_id=message_id
    )
    db.session.add(new_pj)


def save_attachments(files, demande_id=None, message_id=None):
    if not files:
        return

    if not isinstance(files, (list, tuple)):
        files = list(files) if hasattr(files, '__iter__') else [files]

    upload_folder = current_app.config['UPLOAD_FOLDER']
    subfolder, prefix = _get_attachment_path_info(demande_id, message_id)

    if subfolder:
        target_folder = os.path.join(upload_folder, subfolder)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

    for i, file in enumerate(files):
        _save_single_file(file, i, prefix, subfolder, upload_folder, demande_id, message_id, len(files))
    db.session.commit()
