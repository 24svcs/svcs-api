from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If this is a ValidationError, reformat it
    if response is not None and hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # For field errors, flatten the structure
            error_message = next(iter(exc.detail.values()))[0] if exc.detail else "Validation error"
            response.data = {"error": error_message}
        else:
            # For non-field errors
            response.data = {"error": str(exc.detail[0]) if isinstance(exc.detail, list) else str(exc.detail)}
    
    return response