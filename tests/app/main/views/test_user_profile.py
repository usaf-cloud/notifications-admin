import json
import uuid

import pytest
from flask import url_for
from notifications_utils.url_safe_token import generate_token

from tests.conftest import api_user_active as create_user
from tests.conftest import url_for_endpoint_with_token


def test_should_show_overview_page(
    client_request,
):
    page = client_request.get(('main.user_profile'))
    assert page.select_one('h1').text.strip() == 'Your profile'


def test_should_show_name_page(
    client_request
):
    page = client_request.get(('main.user_profile_name'))
    assert page.select_one('h1').text.strip() == 'Change your name'


def test_should_redirect_after_name_change(
    client_request,
    mock_update_user_attribute,
    mock_email_is_not_already_in_use
):
    client_request.post(
        'main.user_profile_name',
        _data={'new_name': 'New Name'},
        _expected_status=302,
        _expected_redirect=url_for('main.user_profile', _external=True),
    )
    assert mock_update_user_attribute.called is True


def test_should_show_email_page(
    client_request,
):
    page = client_request.get(
        'main.user_profile_email'
    )
    assert page.select_one('h1').text.strip() == 'Change your email address'


def test_should_redirect_after_email_change(
    client_request,
    mock_login,
    mock_email_is_not_already_in_use,
):
    client_request.post(
        'main.user_profile_email',
        _data={'email_address': 'new_notify@notify.gov.uk'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_email_authenticate',
            _external=True,
        )
    )


def test_should_show_authenticate_after_email_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-email'] = 'new_notify@notify.gov.uk'

    page = client_request.get('main.user_profile_email_authenticate')

    assert 'Change your email address' in page.text
    assert 'Confirm' in page.text


def test_should_render_change_email_continue_after_authenticate_email(
    client_request,
    mock_verify_password,
    mock_send_change_email_verification,
):
    with client_request.session_transaction() as session:
        session['new-email'] = 'new_notify@notify.gov.uk'
    page = client_request.post(
        'main.user_profile_email_authenticate',
        data={'password': '12345'},
        _expected_status=200,
    )
    assert 'Click the link in the email to confirm the change to your email address.' in page.text


def test_should_redirect_to_user_profile_when_user_confirms_email_link(
    app_,
    logged_in_client,
    api_user_active,
    mock_update_user_attribute,
):

    token = generate_token(payload=json.dumps({'user_id': api_user_active['id'], 'email': 'new_email@gov.uk'}),
                           secret=app_.config['SECRET_KEY'], salt=app_.config['DANGEROUS_SALT'])
    response = logged_in_client.get(url_for_endpoint_with_token('main.user_profile_email_confirm',
                                                                token=token))

    assert response.status_code == 302
    assert response.location == url_for('main.user_profile', _external=True)


def test_should_show_mobile_number_page(
    client_request,
):
    page = client_request.get(('main.user_profile_mobile_number'))
    assert 'Change your mobile number' in page.text


@pytest.mark.parametrize('phone_number_to_register_with', [
    '+4407700900460',
    '+1800-555-555',
])
def test_should_redirect_after_mobile_number_change(
    client_request,
    phone_number_to_register_with,
):
    client_request.post(
        'main.user_profile_mobile_number',
        _data={'mobile_number': phone_number_to_register_with},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_mobile_number_authenticate',
            _external=True,
        )
    )
    with client_request.session_transaction() as session:
        assert session['new-mob'] == phone_number_to_register_with


def test_should_show_authenticate_after_mobile_number_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-mob'] = '+441234123123'

    page = client_request.get(
        'main.user_profile_mobile_number_authenticate',
    )

    assert 'Change your mobile number' in page.text
    assert 'Confirm' in page.text


def test_should_redirect_after_mobile_number_authenticate(
    client_request,
    mock_verify_password,
    mock_send_verify_code,
):
    with client_request.session_transaction() as session:
        session['new-mob'] = '+441234123123'

    client_request.post(
        'main.user_profile_mobile_number_authenticate',
        _data={'password': '12345667'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile_mobile_number_confirm',
            _external=True,
        )
    )


def test_should_show_confirm_after_mobile_number_change(
    client_request,
):
    with client_request.session_transaction() as session:
        session['new-mob-password-confirmed'] = True
    page = client_request.get(
        'main.user_profile_mobile_number_confirm'
    )

    assert 'Change your mobile number' in page.text
    assert 'Confirm' in page.text


@pytest.mark.parametrize('phone_number_to_register_with', [
    '+4407700900460',
    '+1800-555-555',
])
def test_should_redirect_after_mobile_number_confirm(
    client_request,
    mocker,
    mock_update_user_attribute,
    mock_check_verify_code,
    fake_uuid,
    phone_number_to_register_with,
):
    user_before = create_user(fake_uuid)
    user_after = create_user(fake_uuid)
    user_before.current_session_id = str(uuid.UUID(int=1))
    user_after.current_session_id = str(uuid.UUID(int=2))

    # first time (login decorator) return normally, second time (after 2FA return with new session id)
    mocker.patch('app.user_api_client.get_user', side_effect=[user_before, user_after])

    with client_request.session_transaction() as session:
        session['new-mob-password-confirmed'] = True
        session['new-mob'] = phone_number_to_register_with
        session['current_session_id'] = user_before.current_session_id

    client_request.post(
        'main.user_profile_mobile_number_confirm',
        _data={'sms_code': '12345'},
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile',
            _external=True,
        )
    )

    # make sure the current_session_id has changed to what the API returned
    with client_request.session_transaction() as session:
        assert session['current_session_id'] == user_after.current_session_id


def test_should_show_password_page(
    client_request,
):
    page = client_request.get(('main.user_profile_password'))

    assert page.select_one('h1').text.strip() == 'Change your password'


def test_should_redirect_after_password_change(
    client_request,
    mock_update_user_password,
    mock_verify_password,
):
    client_request.post(
        'main.user_profile_password',
        _data={
            'new_password': 'the new password',
            'old_password': 'the old password',
        },
        _expected_status=302,
        _expected_redirect=url_for(
            'main.user_profile',
            _external=True,
        ),
    )


def test_non_gov_user_cannot_see_change_email_link(
    client_request,
    api_nongov_user_active,
):
    client_request.login(api_nongov_user_active)
    page = client_request.get('main.user_profile')
    assert '<a href="/user-profile/email">' not in str(page)
    assert page.select_one('h1').text.strip() == 'Your profile'


def test_non_gov_user_cannot_access_change_email_page(
    client_request,
    api_nongov_user_active,
):
    client_request.login(api_nongov_user_active)
    client_request.get('main.user_profile_email', _expected_status=403)
