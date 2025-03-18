import re
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from phonenumbers import parse, is_valid_number, NumberParseException, format_number, PhoneNumberFormat

def validate_phone(value, default_region='IN'):
    try:
        # Normalize phone number by removing common formatting characters
        normalized_value = re.sub(r'[\s\-\(\)\.]+', '', value)
        
        # Parse number with a default region if no country code provided
        phone_number = parse(normalized_value, default_region)
        
        if not is_valid_number(phone_number):
            raise serializers.ValidationError(_('Please enter a valid phone number.'))
            
        # Return in E.164 format (+1234567890)
        return format_number(phone_number, PhoneNumberFormat.E164)
        
    except NumberParseException:
        raise serializers.ValidationError(_('Please enter a valid phone number format.'))

