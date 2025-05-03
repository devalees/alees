from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from crum import get_current_user

from .models import AuditLog, AuditActionType
from .utils import log_audit_event, calculate_changes, get_object_repr # Import helpers

# TODO: Move AUDITED_MODELS to project settings (e.g., settings.AUDITED_MODELS)
# Using a hardcoded list for now based on implementation steps
AUDITED_MODELS = [
    # Format: 'app_label.ModelName' - Use full app labels
    'api_v1_organization.Organization', # Corrected app label
    'api_v1_user.UserProfile', # Corrected app label (assuming structure)
    # Add other models mentioned or implied (e.g., Project, Task) as needed
    # 'api_v1_features_project.Project', # Example corrected
    # 'api_v1_features_tasks.Task',     # Example corrected
]

# --- Helper Functions (Consider moving to utils if complex) ---

def get_model_from_string(model_string):
    """Helper to get model class from 'app_label.ModelName' string."""
    try:
        app_label, model_name = model_string.split('.')
        return apps.get_model(app_label=app_label, model_name=model_name)
    except (ValueError, LookupError):
        # Log error or handle gracefully if model string is invalid
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not find model for string: {model_string}")
        return None

def get_org_from_instance(instance):
    """
    Attempts to find the relevant Organization context from an instance.
    This needs to be adapted based on common patterns in the project's models.
    """
    # Direct attribute
    if hasattr(instance, 'organization') and instance.organization:
        return instance.organization

    # Via a related user's profile (common pattern)
    if hasattr(instance, 'user') and instance.user:
        profile = getattr(instance.user, 'profile', None) # User might not have a profile link yet
        if profile and hasattr(profile, 'primary_organization') and profile.primary_organization:
             return profile.primary_organization

    # Via a direct link to user who might have an org
    if hasattr(instance, 'created_by') and instance.created_by:
         profile = getattr(instance.created_by, 'profile', None)
         if profile and hasattr(profile, 'primary_organization') and profile.primary_organization:
              return profile.primary_organization

    # If the instance *is* an Organization
    # Use isinstance for more robust checking
    try:
        OrganizationModel = apps.get_model(app_label='api_v1_organization', model_name='Organization')
        if isinstance(instance, OrganizationModel):
            return instance
    except LookupError:
        pass # Handle case where Organization model isn't found

    # TODO: Add more ways to find organization context if needed based on project structure
    # Example: Check for project -> client -> organization pattern
    # if hasattr(instance, 'project') and instance.project:
    #     if hasattr(instance.project, 'client') and instance.project.client:
    #           return instance.project.client # Assuming Client *is* an Org or links to one

    return None # Could not determine organization context


# --- Signal Receivers ---

@receiver(post_save, dispatch_uid="audit_post_save_generic")
def audit_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    """Audit model CREATE and UPDATE events for models in AUDITED_MODELS."""
    # --- Debug Print --- 
    print(f">>> DEBUG: audit_post_save triggered: sender={sender.__name__}, instance={instance}, created={created}")
    # --- End Debug Print ---
    
    # Construct app_label.model_name string for checking
    # Use lower() for case-insensitive matching against AUDITED_MODELS
    model_label = f"{sender._meta.app_label}.{sender._meta.model_name.lower()}"

    # Ignore fixture loading and non-audited models
    # Ensure AUDITED_MODELS list is also lowercased for comparison
    if raw or model_label not in [m.lower() for m in AUDITED_MODELS]:
        return

    # Prioritize user from instance fields, fallback to crum
    instance_user = getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)
    user = instance_user or get_current_user()

    organization = get_org_from_instance(instance)
    action = AuditActionType.CREATE if created else AuditActionType.UPDATE
    changes = None

    # Placeholder for change calculation (Needs improvement)
    if not created:
        changes = calculate_changes(instance, update_fields)

    log_audit_event(
        user=user,
        organization=organization,
        action_type=action,
        content_object=instance,
        changes=changes,
    )

@receiver(post_delete)
def audit_post_delete(sender, instance, using, **kwargs):
    """Audit model DELETE events for models in AUDITED_MODELS."""
    model_label = f"{sender._meta.app_label}.{sender._meta.model_name.lower()}"
    if model_label not in [m.lower() for m in AUDITED_MODELS]:
        return

    # Prioritize user from instance fields (often not available on delete, but try), fallback to crum
    instance_user = getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)
    user = instance_user or get_current_user()

    organization = get_org_from_instance(instance)
    # Capture representation *before* the instance is fully gone
    obj_repr = get_object_repr(instance)

    log_audit_event(
        user=user,
        organization=organization,
        action_type=AuditActionType.DELETE,
        content_object=instance, # Pass instance to get ContentType/PK before delete
        object_repr_override=obj_repr # Use the captured representation
    )


# --- Auth Signals ---

@receiver(user_logged_in)
def audit_user_logged_in(sender, request, user, **kwargs):
    """Audit successful user login events."""
    organization = None
    profile = getattr(user, 'profile', None)
    if profile and hasattr(profile, 'primary_organization') and profile.primary_organization:
         organization = profile.primary_organization

    # Explicitly pass context derived from request
    context = {}
    ip = request.META.get('REMOTE_ADDR')
    if ip:
        context['ip_address'] = ip

    log_audit_event(
        user=user,
        organization=organization,
        action_type=AuditActionType.LOGIN_SUCCESS,
        context=context or None # Pass context if found, else None
    )

@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    """Audit failed user login attempts."""
    username = credentials.get('username')
    # Explicitly pass context derived from request and credentials
    context = {}
    ip = request.META.get('REMOTE_ADDR')
    if ip:
        context['ip_address'] = ip
    if username:
        context['username_attempt'] = username

    log_audit_event(
        user=None,
        action_type=AuditActionType.LOGIN_FAILED,
        context=context or None # Pass context if found, else None
    )

@receiver(user_logged_out)
def audit_user_logged_out(sender, request, user, **kwargs):
    """Audit user logout events."""
    # Explicitly pass context derived from request
    logout_context = {}
    ip = request.META.get('REMOTE_ADDR')
    if ip:
        logout_context['ip_address'] = ip

    if user and user.is_authenticated:
         organization = None
         profile = getattr(user, 'profile', None)
         if profile and hasattr(profile, 'primary_organization') and profile.primary_organization:
              organization = profile.primary_organization

         log_audit_event(
             user=user,
             organization=organization,
             action_type=AuditActionType.LOGOUT,
             context=logout_context or None
         )
    else:
         log_audit_event(
              user=None,
              action_type=AuditActionType.LOGOUT,
              context=logout_context or None
         )

# Note: Dynamic connection based on settings.AUDITED_MODELS or M2M signal handling
# is not implemented here as per the simple steps, but should be considered.
