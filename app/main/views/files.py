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
@login_required
@user_has_permissions('send_messages')
def files(service_id):

    form = FileUploadForm()

    if form.validate_on_submit():
        return redirect(url_for('.files_check', service_id=current_service.id, original_file_name=form.file.data.filename))

    return render_template(
        'views/files/index.html',
        form=form,
    )


@main.route("/service/<service_id>/files/check", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_check(service_id):

    form = FileSendForm()

    return render_template(
        'views/files/check.html',
        filename=request.args.get('original_file_name'),
        form=form,
    )


@main.route("/service/<service_id>/files/new-collection", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_new_collection(service_id):

    form = NewFileCollectionForm()

    if form.validate_on_submit():
        return redirect(url_for(
            'main.files_collection',
            service_id=service_id,
            name=form.name.data,
        ))

    return render_template(
        'views/files/new-collection.html',
        filename=request.args.get('original_file_name'),
        form=form,
    )


@main.route("/service/<service_id>/files/collection", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_collection(service_id):

    return render_template(
        'views/files/collection.html',
        name=request.args.get('name'),
    )


@main.route("/service/<service_id>/files/new-list", methods=['GET', 'POST'])
@login_required
@user_has_permissions('send_messages')
def files_new_list(service_id):

    form = FileUploadForm()

    return render_template(
        'views/files/new-list.html',
        form=form,
    )
