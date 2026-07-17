from flask_login import current_user

from setup import log, csrf, db
from fuction_app import get_private_token_by_git_id, update_gitlab_data, get_milestone_by_git_id, add_milestone, \
    add_issue, get_issue_by_git_id, get_app_id_by_git_id, get_label_by_git_id, add_label, add_link_label_issue, \
    rm_link_label_issue, update_link_issue_miilestone
from flask import request, jsonify, abort, Blueprint, redirect, url_for

gitlab_routes = Blueprint('gitlab_routes', __name__)


def _handle_issue_event(payload, app_id):
    new_issue_data = payload['object_attributes']
    issue = get_issue_by_git_id(new_issue_data['iid'], app_id)
    
    if issue is None:
        issue = add_issue(new_issue_data, app_id)
    else:
        issue.title = new_issue_data['title']
        issue.description = new_issue_data['description']
        issue.is_closed = new_issue_data['state'] == 'closed'
        db.session.commit()

    # Sync labels
    rm_link_label_issue(issue.issue_id)
    for label_data in new_issue_data['labels']:
        label = get_label_by_git_id(label_data['id'], app_id)
        if label is None:
            label = add_label(label_data, app_id)
        else:
            label.title = label_data['title']
            label.description = label_data['description']
            label.color = label_data['color']
            db.session.commit()
        add_link_label_issue(label.label_id, issue.issue_id)

    # Sync milestone
    milestone_git_id = new_issue_data.get('milestone_id')
    milestone_db_id = None
    if milestone_git_id:
        milestone = get_milestone_by_git_id(milestone_git_id, app_id)
        if milestone:
            milestone_db_id = milestone.milestone_id
    
    update_link_issue_miilestone(milestone_db_id, issue)

def _handle_milestone_event(payload, app_id):
    new_milestone = payload['object_attributes']
    milestone = get_milestone_by_git_id(new_milestone['id'], app_id)
    if milestone is None:
        add_milestone(new_milestone, app_id)
    else:
        milestone.title = new_milestone['title']
        milestone.description = new_milestone['description']
        milestone.start_date = new_milestone['start_date']
        milestone.due_date = new_milestone['due_date']
        milestone.is_closed = new_milestone['state'] == 'closed'
        milestone.is_deleted = payload["action"] == 'deleted'
        db.session.commit()

@gitlab_routes.route('/gitlab-webhook', methods=['POST'])
@csrf.exempt
def gitlab_webhook():
    signature = request.headers.get('X-Gitlab-Token')
    app_git_id = request.headers.get('X-Gitlab-App-Id')
    app_id = get_app_id_by_git_id(app_git_id)
    SECRET_TOKEN = get_private_token_by_git_id(app_git_id)

    if signature != SECRET_TOKEN:
        abort(403, description="Signature invalide")

    payload = request.json
    event = request.headers.get('X-Gitlab-Event')

    if event == "Issue Hook":
        _handle_issue_event(payload, app_id)
    elif event == "Milestone Hook":
        _handle_milestone_event(payload, app_id)

    return jsonify({"status": "success"}), 200


@gitlab_routes.route('/gitlab-update', methods=['GET'])
def gitlab_update():
    if current_user.user_id not in (1, 2):
        return redirect(url_for('app_routes.index'))
    update_gitlab_data()
    return "Voilà"
