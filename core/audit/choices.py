from django.utils.translation import gettext_lazy as _

class AuditActionType:
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    PERMISSION_ASSIGN = 'PERMISSION_ASSIGN'
    PERMISSION_REVOKE = 'PERMISSION_REVOKE'
    SYSTEM_EVENT = 'SYSTEM_EVENT'
    # ... add more specific types as needed

    CHOICES = [
        (CREATE, _('Create')),
        (UPDATE, _('Update')),
        (DELETE, _('Delete')),
        (LOGIN_SUCCESS, _('Login Success')),
        (LOGIN_FAILED, _('Login Failed')),
        (LOGOUT, _('Logout')),
        (PERMISSION_ASSIGN, _('Permission Assigned')),
        (PERMISSION_REVOKE, _('Permission Revoked')),
        (SYSTEM_EVENT, _('System Event')),
        # ...
    ]
