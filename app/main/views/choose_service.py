from flask import render_template, redirect, url_for, session
from flask_login import login_required, current_user
from app.main import main
from app import service_api_client
from app.notify_client.service_api_client import ServicesBrowsableItem
from app.utils import is_gov_user


@main.route("/services")
@login_required
def choose_service():
    return render_template(
        'views/choose-service.html',
        services=[ServicesBrowsableItem(x) for x in
                  service_api_client.get_active_services({'user_id': current_user.id})['data']],
        can_add_service=is_gov_user(current_user.email_address)
    )


@main.route("/services-or-dashboard")
def show_all_services_or_dashboard():

    if not current_user.is_authenticated:
        return redirect(url_for('.index'))

    services = service_api_client.get_active_services({'user_id': current_user.id})['data']
    session['service_id'] = services[-1]['id']
    return redirect(url_for('.org_reports'))
