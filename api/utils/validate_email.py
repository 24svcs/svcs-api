from email_validator import validate_email as email_validator, EmailNotValidError
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from org.models import Organization, OrganizationMemberInvitation

def validate_email(value, instance=None):
    """
    Validates organization email format and business rules.
    """
    try:
        # Normalize and validate email (includes DNS check)
        validation = email_validator(value, check_deliverability=True)
        normalized_email = validation.normalized
        
        # Check for uniqueness
        query = Organization.objects.filter(email__iexact=normalized_email)
        if instance:
            query = query.exclude(id=instance.id)
        if query.exists():
            raise serializers.ValidationError(_('A organization with this email already exists.'))
        
        # Check for disposable email domains
        domain = normalized_email.split('@')[1]
        disposable_domains = {
            'tempmail.com', 'throwawaymail.com', 'mailinator.com', 
            'guerrillamail.com', 'sharklasers.com', 'yopmail.com',
            'temp-mail.org', '10minutemail.com', 'trashmail.com',
        }
        
        if domain.lower() in disposable_domains:
            raise serializers.ValidationError(
                _('Please use a permanent email address. Disposable email addresses are not allowed.')
            )
            
        return normalized_email
        
    except EmailNotValidError as e:
        raise serializers.ValidationError(str(e))


def validate_email_invitation(value, organization_id, instance=None):
    """
    Validates organization email format and business rules.
    Ensures the same organization cannot send multiple invitations to the same email
    if the first invitation is pending or accepted.
    """
    try:
        # Normalize and validate email (includes DNS check)
        validation = email_validator(value, check_deliverability=True)
        normalized_email = validation.normalized
        
        # Check for existing invitation with same email for the same organization
        query = OrganizationMemberInvitation.objects.filter(
            email__iexact=normalized_email,
            organization_id=organization_id,
            status__in=[OrganizationMemberInvitation.PENDING, OrganizationMemberInvitation.ACCEPTED]
        )
        
        if instance:
            query = query.exclude(id=instance.id)
            
        if query.exists():
            raise serializers.ValidationError(_('An invitation for this email already exists for this organization.'))
        
        return normalized_email
        
    except EmailNotValidError as e:
        raise serializers.ValidationError(str(e))
