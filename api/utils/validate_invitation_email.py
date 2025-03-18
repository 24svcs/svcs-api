from rest_framework import serializers
from email_validator import validate_email as email_validator, EmailNotValidError
from org.models import OrganizationMemberInvitation
from django.utils.translation import gettext_lazy as _


def validate_email_invitation(value, organization_id, instance=None):
    """
    Validates company email format and business rules.
    Ensures the same company cannot send multiple invitations to the same email
    if the first invitation is pending or accepted.
    """
    try:
        # Normalize and validate email (includes DNS check)
        validation = email_validator(value, check_deliverability=True)
        normalized_email = validation.normalized
        
        # Check for existing invitation with same email for the same company
        query = OrganizationMemberInvitation.objects.filter(
            email__iexact=normalized_email,
            organization_id=organization_id,
            status__in=[OrganizationMemberInvitation.PENDING, OrganizationMemberInvitation.ACCEPTED]
        )
        
        if instance:
            query = query.exclude(id=instance.id)
            
        if query.exists():
            raise serializers.ValidationError(_('An invitation for this email already exists for this company.'))
        
        return normalized_email
        
    except EmailNotValidError as e:
        raise serializers.ValidationError(str(e))
