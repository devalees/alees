import logging
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import smart_str
from crum import get_current_request

from .models import AuditLog # Relative import within the app

logger = logging.getLogger(__name__)

def get_object_repr(instance):
    """Get a limited string representation of the object."""
    if instance is None:
        return None
    try:
        # Use smart_str for potential non-ASCII chars and limit length
        return smart_str(instance)[:255]
    except Exception:
        # Fallback representation if str() fails
        return f"<{instance._meta.verbose_name} object ({instance.pk})>"

def calculate_changes(instance, update_fields=None):
    """
    Calculates the changes dictionary for an UPDATE event.
    Placeholder: Actual diffing logic is complex and needs careful implementation.
    This might involve fetching the object from the DB before save or using
    a library like django-dirtyfields or comparing fields directly if old
    values are somehow available in the signal handler.

    Returns None if no changes detected or not applicable.
    """
    # TODO: Implement robust change detection logic, potentially requiring
    # integration with signals to capture pre-save state.
    # Basic example: return update_fields if available, but this doesn't
    # provide old/new values.
    # if update_fields:
    #     return {"updated_fields": list(update_fields)}
    return None # Placeholder - no change calculation yet

def get_request_context():
    """Extract basic context (like IP address) from the current request via crum."""
    request = get_current_request()
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        # Add other desired context here, e.g.:
        # user_agent = request.META.get('HTTP_USER_AGENT')
        # session_key = request.session.session_key
        context = {}
        if ip_address:
            context['ip_address'] = ip_address
        # if user_agent:
        #     context['user_agent'] = user_agent[:255] # Limit length
        # if session_key:
        #     context['session_key'] = session_key
        return context if context else None # Return None if no context found
    return None

def log_audit_event(
    user, action_type, content_object=None, organization=None,
    changes=None, context=None, object_repr_override=None
):
    """Creates an AuditLog entry, handling context merging and error logging."""
    # --- Debug Print --- 
    print(f">>> DEBUG: log_audit_event called: action={action_type}, user={user}, obj={content_object}, org={organization}")
    # --- End Debug Print ---

    ctype = None
    object_id_str = None
    obj_repr = object_repr_override

    if content_object:
        try:
            ctype = ContentType.objects.get_for_model(content_object)
            # Ensure pk exists before trying to stringify it
            if content_object.pk is not None:
                object_id_str = str(content_object.pk)
            if obj_repr is None: # Only get default repr if not overridden
                obj_repr = get_object_repr(content_object)
        except Exception as e:
            logger.error(f"Error getting ContentType or PK for {content_object}: {e}", exc_info=True)
            # Decide if you still want to log without the object link
            # obj_repr = obj_repr or "<Error getting object details>"

    # TODO: Implement sensitive field masking for 'changes' dict here
    # if changes:
    #     changes = mask_sensitive_data(changes) # Need to define this function

    # Get context from request (IP address, etc.)
    request_context = get_request_context()

    # Merge explicit context with request context
    final_context = {}
    if request_context:
        final_context.update(request_context)
    if context:
        final_context.update(context) # Explicit context overrides request context on collision

    try:
        AuditLog.objects.create(
            user=user,
            organization=organization,
            action_type=action_type,
            content_type=ctype,
            object_id=object_id_str,
            object_repr=obj_repr or "", # Use empty string if obj_repr is None or empty
            changes=changes,
            context=final_context or None # Store None if empty
        )
    except Exception as e:
        # Log the error, but don't let logging failure crash the main operation
        logger.error(f"Failed to create AuditLog entry: {e}", exc_info=True) 