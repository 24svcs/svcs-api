from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
from rest_framework import serializers
from django.conf import settings
import re

def validate_url(value):
    """
    Validates a company logo URL against various criteria:
    - Format validation (must be a valid URL)
    - Content validation (must point to an image file)
    - Security validation (must use https for production)
    
    Args:
        value: The company logo URL to validate
    
    Returns:
        The validated logo URL.
    
    Raises:
        ValidationError: If the logo URL fails any validation checks.
    """
    if not value:
        return value
        
    # Normalize URL
    value = value.strip()
    
    # Validate URL format
    url_validator = URLValidator()
    try:
        url_validator(value)
    except:
        raise serializers.ValidationError(_('Invalid URL format. Please provide a valid URL.'))
    
    # Check for secure URL (https)
    if not value.startswith('https://') and not settings.DEBUG:
        raise serializers.ValidationError(_('Logo URL must use HTTPS for security.'))
    
    # Check if URL points to an image file
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']
    # First check common image hosting patterns
    is_valid_image = False
    
    # Check file extension pattern
    for ext in valid_extensions:
        if value.lower().endswith(ext):
            is_valid_image = True
            break
    
    # Check common image hosting services patterns
    image_hosting_patterns = [
        r'imgur\.com',
        r'cloudinary\.com.*\.(jpg|jpeg|png|gif|svg|webp)',
        r's3\.amazonaws\.com.*\.(jpg|jpeg|png|gif|svg|webp)',
        r'googleusercontent\.com.*\.(jpg|jpeg|png|gif|svg|webp)',
        r'cloudfront\.net.*\.(jpg|jpeg|png|gif|svg|webp)',
        r'res\.cloudinary\.com'
    ]
    
    if not is_valid_image:
        for pattern in image_hosting_patterns:
            if re.search(pattern, value.lower()):
                is_valid_image = True
                break
    
    if not is_valid_image:
        raise serializers.ValidationError(_('Logo URL must point to an image file (.jpg, .jpeg, .png, .gif, .svg, or .webp).'))
    
    # Check URL length
    if len(value) > 2048:  # Standard max URL length
        raise serializers.ValidationError(_('Logo URL is too long.'))
    
    return value
