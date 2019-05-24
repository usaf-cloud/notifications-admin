from flask import abort, current_app, request, session
from flask_login import AnonymousUserMixin, UserMixin, login_user
from notifications_python_client.errors import HTTPError
from werkzeug.utils import cached_property

from app.models.organisation import Organisation
from app.models.roles_and_permissions import (
    all_permissions, translate_permissions_from_db_to_admin_roles
)
from app.notify_client import InviteTokenError
from app.notify_client.invite_api_client import invite_api_client
from app.notify_client.org_invite_api_client import org_invite_api_client
from app.notify_client.organisations_api_client import organisations_client
from app.notify_client.user_api_client import user_api_client
from app.utils import is_gov_user


def _get_service_id_from_view_args():
    return str(request.view_args.get('service_id', '')) or None


def _get_org_id_from_view_args():
    return str(request.view_args.get('org_id', '')) or None


class User(UserMixin):
    def __init__(self, fields):
        self.id = fields.get('id')
        self.name = fields.get('name')
        self.email_address = fields.get('email_address')
        self.mobile_number = fields.get('mobile_number')
        self.password_changed_at = fields.get('password_changed_at')
        self._set_permissions(fields.get('permissions', {}))
        self.auth_type = fields.get('auth_type')
        self.failed_login_count = fields.get('failed_login_count')
        self.state = fields.get('state')
        self.max_failed_login_count = current_app.config["MAX_FAILED_LOGIN_COUNT"]
        self.logged_in_at = fields.get('logged_in_at')
        self.platform_admin = fields.get('platform_admin')
        self.current_session_id = fields.get('current_session_id')
        self.services = fields.get('services', [])
        self.organisations = fields.get('organisations', [])

    @classmethod
    def from_id(cls, user_id):
        return cls(user_api_client.get_user(user_id))

    @classmethod
    def from_email_address(cls, email_address):
        return cls(user_api_client.get_user_by_email(email_address))

    @classmethod
    def from_email_address_or_none(cls, email_address):
        response = user_api_client.get_user_by_email_or_none(email_address)
        if response:
            return cls(response)
        return None

    @staticmethod
    def already_registered(email_address):
        return bool(User.from_email_address_or_none(email_address))

    @classmethod
    def from_email_address_and_password_or_none(cls, email_address, password):
        user = cls.from_email_address_or_none(email_address)
        if not user:
            return None
        if user.locked:
            return None
        if not user_api_client.verify_password(user.id, password):
            return None
        return user

    def _set_permissions(self, permissions_by_service):
        """
        Permissions is a dict {'service_id': ['permission a', 'permission b', 'permission c']}

        The api currently returns some granular permissions that we don't set or use separately (but may want
        to in the future):
        * send_texts, send_letters and send_emails become send_messages
        * manage_user and manage_settings become
        users either have all three permissions for a service or none of them, they're not helpful to distinguish
        between on the front end. So lets collapse them into "send_messages" and "manage_service". If we want to split
        them out later, we'll need to rework this function.
        """
        self._permissions = {
            service: translate_permissions_from_db_to_admin_roles(permissions)
            for service, permissions
            in permissions_by_service.items()
        }

    def update(self, **kwargs):
        response = user_api_client.update_user_attribute(self.id, **kwargs)
        self.__init__(response)

    def update_password(self, password):
        response = user_api_client.update_password(self.id, password)
        self.__init__(response)

    def set_permissions(self, service_id, permissions, folder_permissions):
        user_api_client.set_user_permissions(
            self.id,
            service_id,
            permissions=permissions,
            folder_permissions=folder_permissions,
        )

    def logged_in_elsewhere(self):
        # if the current user (ie: db object) has no session, they've never logged in before
        return self.current_session_id is not None and session.get('current_session_id') != self.current_session_id

    def activate(self):
        if self.state == 'pending':
            user_data = user_api_client.activate_user(self.id)
            return self.__class__(user_data['data'])
        else:
            return self

    def login(self):
        login_user(self)

    def reset_failed_login_count(self):
        user_api_client.reset_failed_login_count(self.id)

    @property
    def is_active(self):
        return self.state == 'active'

    @property
    def is_gov_user(self):
        return is_gov_user(self.email_address)

    @property
    def is_authenticated(self):
        return (
            not self.logged_in_elsewhere() and
            super(User, self).is_authenticated
        )

    @property
    def permissions(self):
        return self._permissions

    @permissions.setter
    def permissions(self, permissions):
        raise AttributeError("Read only property")

    def has_permissions(self, *permissions, restrict_admin_usage=False):
        unknown_permissions = set(permissions) - all_permissions
        if unknown_permissions:
            raise TypeError('{} are not valid permissions'.format(list(unknown_permissions)))

        # Service id is always set on the request for service specific views.
        service_id = _get_service_id_from_view_args()
        org_id = _get_org_id_from_view_args()

        if not service_id and not org_id:
            # we shouldn't have any pages that require permissions, but don't specify a service or organisation.
            # use @user_is_platform_admin for platform admin only pages
            raise NotImplementedError

        # platform admins should be able to do most things (except eg send messages, or create api keys)
        if self.platform_admin and not restrict_admin_usage:
            return True

        if org_id:
            return org_id in self.organisations
        if not permissions:
            return service_id in self.services
        if service_id:
            return any(x in self._permissions.get(service_id, []) for x in permissions)

    def has_permission_for_service(self, service_id, permission):
        return permission in self._permissions.get(service_id, [])

    def has_template_folder_permission(self, template_folder, service=None):
        if self.platform_admin:
            return True

        # Top-level templates are always visible
        if template_folder is None or template_folder['id'] is None:
            return True

        return self.id in template_folder.get("users_with_permission", [])

    def template_folders_for_service(self, service=None):
        """
        Returns list of template folders that a user can view for a given service
        """
        return [
            template_folder
            for template_folder in service.all_template_folders
            if self.id in template_folder.get("users_with_permission", [])
        ]

    @cached_property
    def _services(self):
        return user_api_client.get_services_for_user(self.id)

    @property
    def trial_mode_services(self):
        pass

    def belongs_to_service(self, service_id):
        return str(service_id) in self.services

    def belongs_to_service_or_403(self, service_id):
        if not self.belongs_to_service(service_id):
            abort(403)

    @property
    def locked(self):
        return self.failed_login_count >= self.max_failed_login_count

    @property
    def email_domain(self):
        return self.email_address.split('@')[-1]

    @cached_property
    def default_organisation(self):
        return Organisation(
            organisations_client.get_organisation_by_domain(self.email_domain)
        )

    @property
    def default_organisation_type(self):
        if self.default_organisation:
            return self.default_organisation.organisation_type
        if self.has_nhs_email_address:
            return 'nhs'
        return None

    @property
    def has_nhs_email_address(self):
        return self.email_address.lower().endswith((
            '@nhs.uk', '.nhs.uk', '@nhs.net', '.nhs.net',
        ))

    def serialize(self):
        dct = {
            "id": self.id,
            "name": self.name,
            "email_address": self.email_address,
            "mobile_number": self.mobile_number,
            "password_changed_at": self.password_changed_at,
            "state": self.state,
            "failed_login_count": self.failed_login_count,
            "permissions": [x for x in self._permissions],
            "organisations": self.organisations,
            "current_session_id": self.current_session_id
        }
        if hasattr(self, '_password'):
            dct['password'] = self._password
        return dct

    @classmethod
    def register(
        cls,
        name,
        email_address,
        mobile_number,
        password,
        auth_type,
    ):
        return cls(user_api_client.register_user(
            name,
            email_address,
            mobile_number or None,
            password,
            auth_type,
        ))

    def set_password(self, pwd):
        self._password = pwd

    def send_verify_email(self):
        user_api_client.send_verify_email(self.id, self.email_address)

    def send_verify_code(self, to=None):
        user_api_client.send_verify_code(self.id, 'sms', to or self.mobile_number)

    def send_already_registered_email(self):
        user_api_client.send_already_registered_email(self.id, self.email_address)

    def get_new_session_id(self):
        return self.__class__(user_api_client.get_user(self.id)).current_session_id


class InvitedUser(object):

    def __init__(self,
                 id,
                 service,
                 from_user,
                 email_address,
                 permissions,
                 status,
                 created_at,
                 auth_type,
                 folder_permissions):
        self.id = id
        self.service = str(service)
        self._from_user = from_user
        self.email_address = email_address
        if isinstance(permissions, list):
            self.permissions = permissions
        else:
            if permissions:
                self.permissions = permissions.split(',')
            else:
                self.permissions = []
        self.status = status
        self.created_at = created_at
        self.auth_type = auth_type
        self.permissions = translate_permissions_from_db_to_admin_roles(self.permissions)
        self.folder_permissions = folder_permissions

    @classmethod
    def create(
        cls,
        invite_from_id,
        service_id,
        email_address,
        permissions,
        auth_type,
        folder_permissions,
    ):
        return cls(**invite_api_client.create_invite(
            invite_from_id,
            service_id,
            email_address,
            permissions,
            auth_type,
            folder_permissions,
        ))

    def accept_invite(self):
        invite_api_client.accept_invite(self.service, self.id)

    def add_to_service(self):
        user_api_client.add_user_to_service(
            self.service,
            self.id,
            self.permissions,
            self.folder_permissions,
        )

    @property
    def from_user(self):
        return User.from_id(self._from_user)

    @classmethod
    def from_token(cls, token):
        try:
            return cls(**invite_api_client.check_token(token))
        except HTTPError as exception:
            if exception.status_code == 400 and 'invitation' in exception.message:
                raise InviteTokenError(exception.message['invitation'])
            else:
                raise exception

    def has_permissions(self, *permissions):
        if self.status == 'cancelled':
            return False
        return set(self.permissions) > set(permissions)

    def has_permission_for_service(self, service_id, permission):
        if self.status == 'cancelled':
            return False
        return self.service == service_id and permission in self.permissions

    def __eq__(self, other):
        return ((self.id,
                self.service,
                self._from_user,
                self.email_address,
                self.auth_type,
                self.status) == (other.id,
                other.service,
                other._from_user,
                other.email_address,
                other.auth_type,
                other.status))

    def serialize(self, permissions_as_string=False):
        data = {'id': self.id,
                'service': self.service,
                'from_user': self._from_user,
                'email_address': self.email_address,
                'status': self.status,
                'created_at': str(self.created_at),
                'auth_type': self.auth_type,
                'folder_permissions': self.folder_permissions
                }
        if permissions_as_string:
            data['permissions'] = ','.join(self.permissions)
        else:
            data['permissions'] = sorted(self.permissions)
        return data

    def template_folders_for_service(self, service=None):
        # only used on the manage users page to display the count, so okay to not be fully fledged for now
        return [{'id': x} for x in self.folder_permissions]


class InvitedOrgUser(object):

    def __init__(self, id, organisation, invited_by, email_address, status, created_at):
        self.id = id
        self.organisation = str(organisation)
        self._invited_by = invited_by
        self.email_address = email_address
        self.status = status
        self.created_at = created_at

    def __eq__(self, other):
        return ((self.id,
                self.organisation,
                self._invited_by,
                self.email_address,
                self.status) == (other.id,
                other.organisation,
                other._invited_by,
                other.email_address,
                other.status))

    @classmethod
    def create(cls, invite_from_id, org_id, email_address):
        return cls(**org_invite_api_client.create_invite(
            invite_from_id, org_id, email_address
        ))

    def serialize(self, permissions_as_string=False):
        data = {'id': self.id,
                'organisation': self.organisation,
                'invited_by': self._invited_by,
                'email_address': self.email_address,
                'status': self.status,
                'created_at': str(self.created_at)
                }
        return data

    @property
    def invited_by(self):
        return User.from_id(self._invited_by)

    @classmethod
    def from_token(cls, token):
        try:
            return cls(**org_invite_api_client.check_token(token))
        except HTTPError as exception:
            if exception.status_code == 400 and 'invitation' in exception.message:
                raise InviteTokenError(exception.message['invitation'])
            else:
                raise exception


class AnonymousUser(AnonymousUserMixin):
    # set the anonymous user so that if a new browser hits us we don't error http://stackoverflow.com/a/19275188

    # THIS SHOULDN’T BE NEEDED
    platform_admin = False

    def logged_in_elsewhere(self):
        return False

    @property
    def default_organisation(self):
        return Organisation(None)


class Users:

    @staticmethod
    def for_service(service_id):
        return [
            User(user)
            for user in user_api_client.get_users_for_service(service_id)
        ]

    @staticmethod
    def for_organisation(org_id):
        return [
            User(user)
            for user in user_api_client.get_users_for_organisation(org_id)
        ]


class InvitedUsers:

    @staticmethod
    def for_service(service_id):
        return [
            InvitedUser(**invite)
            for invite in invite_api_client.get_invites_for_service(service_id)
            if invite['status'] != 'accepted'
        ]

    @staticmethod
    def for_organisation(org_id):
        return [
            InvitedOrgUser(**invite)
            for invite in org_invite_api_client.get_invites_for_organisation(org_id)
            if invite['status'] != 'accepted'
        ]


class UsersAndInvitedUsers:

    @staticmethod
    def for_organisation(org_id):
        return sorted(
            Users.for_organisation(org_id) + InvitedUsers.for_organisation(org_id),
            key=lambda user: user.email_address,
        )
