from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from api.utils import (
    validate_email, validate_phone, validate_tax, validate_url, validate_org_name, validate_org_name_space
)
from phonenumber_field.modelfields import PhoneNumberField
from django.db import transaction
from core.models import Permission
import pytz
from django.utils import timezone as tz
from api.utils.tz import convert_datetime_to_timezone
from org.models import Organization, OrganizationMember
from core.models import User

def validate_company_user_id(value):
    query = Organization.objects.filter(user_id=value).exists()
    if query:
        raise serializers.ValidationError(_('Can not create another Organization with the same user'))
    return value


class SimpleOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'name_space', 'email', 'logo_url' 
    ]



#            'role', 

class OrganizationSerializer(serializers.ModelSerializer):
    member_limit = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'name_space', 'email', 'phone', 'tax_id', 'organization_type', 'industry', 'is_verified', 'description', 'logo_url',  'member_count',  'member_limit', 'role',   'created_at','updated_at',
            
        ]
    
    
    def get_member_limit(self, obj):
        return obj.get_member_limit()
    
    def get_available_members(self, obj):
        return obj.get_available_members()
    
    def get_member_count(self, obj):
        return obj.members.count()
    
    def get_can_add_member(self, obj):
        return obj.can_add_member()
    
    
    def to_representation(self, instance):
        """
        Convert datetime fields to the requested timezone
        """
        representation = super().to_representation(instance)
        
        # Get timezone from context (set by TimezoneMixin)
        timezone = self.context.get('timezone', pytz.UTC)
        
        # Convert datetime fields
        datetime_fields = ['created_at', 'updated_at']
        for field in datetime_fields:
            if representation.get(field):
                # Parse the datetime string
                dt = tz.datetime.fromisoformat(representation[field].replace('Z', '+00:00'))
                # Use the utility function for conversion
                converted_dt = convert_datetime_to_timezone(dt, timezone)
                # Format back to ISO 8601
                representation[field] = converted_dt.isoformat()
        
        return representation
    
    
    def get_role(self, obj):
        request = self.context.get('request')
        user = None
        
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
        else:
            user_id = self.context.get('user_id')
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return None
        
        if not user:
            return None
            
        try:
            member = OrganizationMember.objects.select_related('organization', 'user').get(organization=obj, user=user)

            if member.is_owner:
                return "Owner"
            elif member.is_admin:
                return "Admin"
            else:
                return "Member"
        except OrganizationMember.DoesNotExist:
            return None




class CreateOrganizationSerializer(serializers.ModelSerializer):
    name =  serializers.CharField(validators=[validate_org_name.validate_organization_name])
    name_space = serializers.CharField(validators=[validate_org_name_space.validate_organization_name_space])
    email = serializers.EmailField(validators=[validate_email.validate_email])
    phone  =  PhoneNumberField(validators=[validate_phone.validate_phone])

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'name_space', 'email',
            'phone', 'tax_id', 'organization_type', 'description', 'industry', 'logo_url', 

        ]

    def validate_tax_id(self, value):
        return validate_tax.validate_tax_id(value)
    
    def validate_user_id(self, value):
        return validate_company_user_id(value)
    
    
    def validate_logo_url(self, value):
        return validate_url.validate_url(value)
    

    
    def create(self, validated_data):
        user_id = self.context.get('user_id')
        
        if not user_id:
            raise serializers.ValidationError(_('Organization can not be created by Anonymous user'))
            
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError(_('User with this ID does not exist.'))
        
        if Organization.all_objects.filter(user_id=user_id).exists():
            raise serializers.ValidationError(_('A company with this user ID already exists.'))

        validated_data['user_id'] = user_id
        
        with transaction.atomic():
            organization = Organization.objects.create(**validated_data)
            permissions = Permission.objects.filter(
                name__in=[choice[0] for choice in Permission.PERMISSION_CHOICES]
            ).all()
            
            member = OrganizationMember.objects.create(
                organization=organization,
                user_id=user_id,
                status=OrganizationMember.ACTIVE,
                is_owner=True,
                is_admin=True,
            )
            member.permissions.add(*permissions)
            return organization



class UpdateOrganizationSerializer(serializers.ModelSerializer):
    phone  =  PhoneNumberField(validators=[validate_phone.validate_phone])
    class Meta:
        model = Organization
        fields = ['name', 'name_space', 'email', 'phone', 'tax_id', 'logo_url', 'is_active', 'description', 'industry' ]

    def validate_name(self, value):
        if not value:
            return value
        return validate_org_name.validate_organization_name(value, self.instance)

    def validate_name_space(self, value):
        if not value:
            return value
        return validate_org_name_space.validate_organization_name_space(value, self.instance)

        
    def validate_tax_id(self, value):
        if not value:
            return value
        return validate_tax.validate_tax_id(value, self.instance)
    
    
    # def validate_logo_url(self, value):
    #     return validate_url.validate_url(value, self.instance)
    
    
    def validate_email(self, value):
        if not value:
            return value
        return validate_email.validate_email(value, self.instance)
    
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
            
        try:
            instance.save()
            return instance
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to update company: {str(e)}")
            raise serializers.ValidationError(_('Failed to update company. Please try again.'))
        
        
        

class TransferOwnershipSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        # Check if user exists with this email
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_('User with this email does not exist.'))

        # Check if user is already an owner of another company
        if Organization.objects.prefetch_related('members').filter(members__user=user, members__is_owner=True).exists():
            raise serializers.ValidationError(_('User is already an owner of another company.'))

        return value

    def transfer_ownership(self, organization):
        user_email = self.validated_data['email']
        new_owner = User.objects.get(email=user_email)
        
        with transaction.atomic():
            # Get all available permissions
            all_permissions = Permission.objects.filter(
                name__in=[choice[0] for choice in Permission.PERMISSION_CHOICES]
            ).all()

            # Remove ownership and permissions from current owner
            current_owner = OrganizationMember.objects.get(organization=organization, is_owner=True)
            current_owner.is_owner = False
            current_owner.is_admin = False
            current_owner.permissions.clear()
            current_owner.save()

            # Check if new owner is already a member
            try:
                new_owner_member = OrganizationMember.objects.get(organization=organization, user=new_owner)
                # Update existing member to owner
                new_owner_member.is_owner = True
                new_owner_member.is_admin = True
                # Clear existing permissions to avoid duplicates
                new_owner_member.permissions.clear()
                new_owner_member.permissions.add(*all_permissions)
                new_owner_member.save()
            except OrganizationMember.DoesNotExist:
                # Create new member as owner
                new_owner_member = OrganizationMember.objects.create(
                    organization=organization,
                    user=new_owner,
                    status=OrganizationMember.ACTIVE,
                    is_owner=True,
                    is_admin=True
                )
                new_owner_member.permissions.add(*all_permissions)

            return organization


class RestoreOrganizationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, validators=[validate_email.validate_email])
    
    class Meta:
        model = Organization
        fields = ['email']
        
    def validate_email(self, value):
        # Check if the email is associated with an inactive organization
        try:
            organization = Organization.all_objects.get(email=value, is_active=False)
        except Organization.DoesNotExist:
            raise serializers.ValidationError(_('No inactive organization found with this email.'))
        
        # Check if the current user is the owner of the organization
        user = self.context.get('request').user
        try:
            member = OrganizationMember.objects.get(
                organization=organization,
                user=user,
                is_owner=True
            )
        except OrganizationMember.DoesNotExist:
            raise serializers.ValidationError(_('You must be the owner of this organization to restore it.'))
        
        # Check for name/namespace conflicts with active organizations
        name_conflict = Organization.objects.filter(name=organization.name).exists()
        namespace_conflict = Organization.objects.filter(name_space=organization.name_space).exists()
        
        conflicts = []
        if name_conflict:
            conflicts.append('name')
        if namespace_conflict:
            conflicts.append('namespace')
        
        if conflicts:
            raise serializers.ValidationError({
                'conflicts': _('Cannot restore organization due to conflicts with existing organizations: {}').format(
                    ', '.join(conflicts)
                )
            })
        
        # Validate member limits
        current_member_count = organization.members.count()
        member_limit = organization.get_member_limit()
        
        if current_member_count > member_limit:
            raise serializers.ValidationError(_(
                'Organization has more members ({}) than allowed by its current type ({}). '
                'Please upgrade the organization type or remove some members before restoring.'
            ).format(current_member_count, member_limit))
        
        return value
    
    def restore_organization(self):
        email = self.validated_data['email']
        organization = Organization.all_objects.get(email=email, is_active=False)
        
        with transaction.atomic():
            # Restore the organization
            organization.is_active = True
            organization.save()
            
            # You might want to reactivate members or perform other related actions
            # For example, reactivate the owner's membership
            OrganizationMember.objects.filter(
                organization=organization,
                is_owner=True
            ).update(status=OrganizationMember.ACTIVE)
            
            # If you have any notification system, you could send a notification here
            # NotificationAlert.objects.create(...)
            
        return organization
