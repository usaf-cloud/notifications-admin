from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import abort

from app import (
    current_service,
)
from app.main import main
from app.main.forms import (
    SearchByNameForm,
    FileUploadForm,
    FileSendForm,
    NewFileCollectionForm,
)
from app.utils import user_has_permissions


@main.route("/service/<service_id>/files", methods=['GET', 'POST'])
@main.route("/service/<service_id>/files/<file_type>", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files(service_id, file_type=None):

    return render_template(
        'views/files/index.html',
        file_type=file_type,
    )


@main.route("/service/<service_id>/files/new-letter", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_new_letter(service_id):

    form = FileUploadForm()

    if form.validate_on_submit():
        return redirect(url_for('.files_check', service_id=current_service.id, original_file_name=form.file.data.filename))

    return render_template(
        'views/files/new-letter.html',
        form=form,
    )


@main.route("/service/<service_id>/files/check", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_check(service_id):

    form = FileSendForm()

    if form.validate_on_submit():
        return redirect(url_for('.files_sent', service_id=current_service.id, original_file_name=request.args.get('original_file_name')))

    return render_template(
        'views/files/check.html',
        filename=request.args.get('original_file_name'),
        form=form,
    )


@main.route("/service/<service_id>/files/new-other", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_new_other(service_id):

    form = FileUploadForm()

    if form.validate_on_submit():
        return redirect(url_for('.files_check_other', service_id=current_service.id, original_file_name=form.file.data.filename))

    return render_template(
        'views/files/new-other.html',
        form=form,
    )


@main.route("/service/<service_id>/files/check-other", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_check_other(service_id):

    return render_template(
        'views/files/check-other.html',
        filename=request.args.get('original_file_name'),
    )


@main.route("/service/<service_id>/files/collection", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_collection(service_id):

    return render_template(
        'views/files/collection.html',
        name=request.args.get('name'),
    )


@main.route("/service/<service_id>/files/letter-sent", methods=['GET'])
@login_required
@user_has_permissions('send_messages')
def files_sent(service_id):

    return render_template(
        'views/files/sent.html',
        filename=request.args.get('original_file_name'),
    )
