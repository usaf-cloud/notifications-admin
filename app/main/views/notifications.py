# -*- coding: utf-8 -*-
from datetime import datetime

from flask import (
    abort,
    render_template,
    jsonify,
    request,
    url_for,
    Response,
    stream_with_context,
    current_app,
)
from flask_login import login_required

from app import (
    notification_api_client,
    job_api_client,
    current_service,
    format_date_numeric,
    service_api_client,
)
from app.main.forms import SearchNotificationsForm
from app.main import main
from app.template_previews import TemplatePreview, get_page_count_for_letter
from app.main.views.jobs import add_preview_of_content_to_notifications
from app.utils import (
    user_has_permissions,
    get_help_argument,
    get_template,
    get_time_left,
    get_letter_timings,
    FAILURE_STATUSES,
    DELIVERED_STATUSES,
    generate_notifications_csv,
    parse_filter_args,
    set_status_filters,
)


@main.route("/services/<service_id>/notification/<uuid:notification_id>")
@login_required
@user_has_permissions('view_activity', admin_override=True)
def view_notification(service_id, notification_id):
    notification = notification_api_client.get_notification(service_id, str(notification_id))
    notification['template'].update({'reply_to_text': notification['reply_to_text']})

    template = get_template(
        notification['template'],
        current_service,
        letter_preview_url=url_for(
            '.view_letter_notification_as_preview',
            service_id=service_id,
            notification_id=notification_id,
            filetype='png',
        ),
        page_count=get_page_count_for_letter(notification['template']),
        show_recipient=False,
        redact_missing_personalisation=True,
    )
    template.values = get_all_personalisation_from_notification(notification)
    if notification['job']:
        job = job_api_client.get_job(service_id, notification['job']['id'])['data']
    else:
        job = None

    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)
    notifications = notification_api_client.get_notifications_for_service(
        service_id=service_id,
        template_type=['sms'],
        status=filter_args.get('status'),
        limit_days=current_app.config['ACTIVITY_STATS_LIMIT_DAYS'],
    )['notifications']
    templates = service_api_client.get_service_templates(service_id)['data']
    return render_template(
        'views/dashboard/casework-home.html',
        notification_id=notification['id'],
        template=template,
        partials=get_single_notification_partials(notification),
        created_by=notification.get('created_by'),
        created_at=notification['created_at'],
        notifications=list(add_preview_of_content_to_notifications(
            notifications
        )),
        search_form=SearchNotificationsForm(),
        show_search_box=len(templates) > 7,
        can_receive_inbound=('inbound_sms' in current_service['permissions']),
        updates_url=url_for(
            ".view_notification_updates",
            service_id=service_id,
            notification_id=notification['id'],
            status=request.args.get('status'),
            help=get_help_argument()
        ),
    )


@main.route("/services/<service_id>/notification/<uuid:notification_id>.<filetype>")
@login_required
@user_has_permissions('view_activity', admin_override=True)
def view_letter_notification_as_preview(service_id, notification_id, filetype):

    if filetype not in ('pdf', 'png'):
        abort(404)

    notification = notification_api_client.get_notification(service_id, notification_id)
    notification['template'].update({'reply_to_text': notification['reply_to_text']})

    template = get_template(
        notification['template'],
        current_service,
        letter_preview_url=url_for(
            '.view_letter_notification_as_preview',
            service_id=service_id,
            notification_id=notification_id,
            filetype='png',
        ),
    )

    template.values = notification['personalisation']

    return TemplatePreview.from_utils_template(template, filetype, page=request.args.get('page'))


@main.route("/services/<service_id>/notification/<notification_id>.json")
@user_has_permissions('view_activity', admin_override=True)
def view_notification_updates(service_id, notification_id):
    return jsonify(**get_single_notification_partials(
        notification_api_client.get_notification(service_id, notification_id)
    ))


def get_single_notification_partials(notification):
    return {
        'notifications': render_template(
            'partials/notifications/notifications.html',
            notification=notification,
            more_than_one_page=False,
            percentage_complete=100,
            time_left=get_time_left(notification['created_at']),
        ),
        'status': render_template(
            'partials/notifications/status.html',
            notification=notification
        ),
    }


def get_all_personalisation_from_notification(notification):

    if notification['template'].get('redact_personalisation'):
        notification['personalisation'] = {}

    if notification['template']['template_type'] == 'email':
        notification['personalisation']['email_address'] = notification['to']

    if notification['template']['template_type'] == 'sms':
        notification['personalisation']['phone_number'] = notification['to']

    return notification['personalisation']


@main.route("/services/<service_id>/download-notifications.csv")
@login_required
@user_has_permissions('view_activity', admin_override=True)
def download_notifications_csv(service_id):
    filter_args = parse_filter_args(request.args)
    filter_args['status'] = set_status_filters(filter_args)

    return Response(
        stream_with_context(
            generate_notifications_csv(
                service_id=service_id,
                job_id=None,
                status=filter_args.get('status'),
                page=request.args.get('page', 1),
                page_size=5000,
                format_for_csv=True,
                template_type=filter_args.get('message_type')
            )
        ),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'inline; filename="{} - {} - {} report.csv"'.format(
                format_date_numeric(datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")),
                filter_args['message_type'][0],
                current_service['name'])
        }
    )
