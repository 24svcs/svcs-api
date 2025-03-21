from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import mixins

from api.mixins import TimezoneMixin
from org.serializers.org import (
    OrganizationSerializer, UpdateOrganizationSerializer,
    TransferOwnershipSerializer, Organization, SimpleOrganizationSerializer,
    RestoreOrganizationSerializer, CreateOrganizationSerializer
)

from org.serializers.member import (
    UpdateInviteOrganizationMemberSerializer,
    CreateInviteOrganizationMemberSerializer,
    InvitedOrganizationMemberSerializer,
    OrganizationMember,
    OrganizationMemberInvitation,
    OrganizationMemberSerializer,
    UpdateOrganizationMemberSerializer,
    
)
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from core.models import Permission
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from api.pagination import CustomPagination
from org.filters import OrganizationFilter
from api.permission import OrganizationPermission


class MyOrganizationViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    permission_classes = [IsAuthenticated]
    
    pagination_class = CustomPagination

    
    def get_queryset(self):
        user_id = self.request.user.id
        return Organization.objects.filter(user_id=user_id).only('id', 'name', 'name_space', 'email', 'logo_url')
    
    
    serializer_class = SimpleOrganizationSerializer
    


class OrganizationViewSet(TimezoneMixin, viewsets.ModelViewSet):
    """
    API endpoint for companies with optimized queries.
    """
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'email', 'tax_id']
    filterset_class = OrganizationFilter 
    
    def get_queryset(self):
        user = self.request.user
        
        if self.action == 'list':
            return Organization.objects.filter(
                members__user=user,
                members__status=OrganizationMember.ACTIVE,
            ).only(
                'id', 'name', 'name_space', 'email', 'logo_url'
            ).distinct()
        else:
            # Optimize with select_related and prefetch_related to avoid N+1 queries
            return Organization.objects.prefetch_related(
                'members',
                'members__user',
                'members__permissions'
            ).select_related(
                # Add any direct foreign key relationships here if needed
            ).filter(
                id=self.kwargs.get('pk'),
                members__user=user,
                members__status=OrganizationMember.ACTIVE,
            ).distinct()


    
    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), OrganizationPermission(Permission.EDIT_ORGANIZATION)]
        elif self.action == 'destroy':
            return [IsAuthenticated(), OrganizationPermission(Permission.DELETE_ORGANIZATION)]
        return [IsAuthenticated()]


    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UpdateOrganizationSerializer
        elif self.action == 'list':
            return SimpleOrganizationSerializer
        elif self.action == 'create':
            return CreateOrganizationSerializer
        return OrganizationSerializer
    
    
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context
    
    
    @action(detail=False, methods=['GET'], url_name='me')
    def my_organization(self, request, pk=None):
        user_id = self.request.user.id
        
        organization = Organization.objects.filter(
            user_id=user_id,
        ).first()
        
        if not organization:
            return Response({'detail': 'No organization found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(organization)
        return Response(serializer.data)
    

    @action(detail=True, methods=['post'], url_path='transfer-ownership', permission_classes=[IsAuthenticated])
    def transfer_ownership(self, request, pk=None):
        organization = self.get_object()

        # Verify current user is the owner
        try:
            member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                is_owner=True
            )
        except OrganizationMember.DoesNotExist:
            return Response(
                {'detail': _('Only the organization owner can transfer ownership.')},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = TransferOwnershipSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.transfer_ownership(organization)
                return Response(
                    {'detail': _('Ownership transferred successfully.')},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='restore', permission_classes=[IsAuthenticated])
    def restore_organization(self, request):
        """
        Restore a soft-deleted organization.
        Only the original owner can restore an organization.
        """
        serializer = RestoreOrganizationSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    organization = serializer.restore_organization()
                    
                    # Reactivate the owner's membership if it was deactivated
                    OrganizationMember.objects.filter(
                        organization=organization,
                        user=request.user,
                        is_owner=True
                    ).update(status=OrganizationMember.ACTIVE)
                    
                    return Response(
                        {'detail': _('Organization restored successfully.'),
                         'id': organization.id},
                        status=status.HTTP_200_OK
                    )
            except Exception as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationMemberViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin
):
    """
    API endpoint for members with optimized queries.
    """
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), OrganizationPermission(Permission.EDIT_ORGANIZATION_MEMBER)]
        elif self.action == 'destroy':
            return [IsAuthenticated(), OrganizationPermission(Permission.DELETE_ORGANIZATION_MEMBER)]
        return [IsAuthenticated()]
    
    
    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return UpdateOrganizationMemberSerializer
        return OrganizationMemberSerializer
    
    def get_queryset(self):
        # Optimize query with select_related and prefetch_related
        return OrganizationMember.objects.filter(
            organization_id=self.kwargs['organization_pk']
        ).select_related(
            'user', 'organization'
        ).prefetch_related(
            'permissions'
        )
    
    def get_serializer_context(self):
        return {'organization_id': self.kwargs['organization_pk']}
    
    def get_filterset_kwargs(self):
        kwargs = super().get_filterset_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def perform_update(self, serializer):
        instance = serializer.instance
        
        # Prevent updating owner membership
        if instance.is_owner:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Owner membership cannot be modified.")
        serializer.save()
    
    
    def perform_destroy(self, instance):
        # Check if the member is the owner
        if instance.is_owner:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot delete the Organization owner's membership.")
            
        with transaction.atomic():
            # Delete associated invitation if it exists
            OrganizationMemberInvitation.objects.filter(
                organization=instance.organization,
                email__iexact=instance.user.email
            ).delete()
            
            # Delete the member
            return super().perform_destroy(instance)


class OrganizationMemberInvitationViewSet(TimezoneMixin,viewsets.ModelViewSet):
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['email']
    
    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated(), OrganizationPermission(Permission.CREATE_MEMBER_INVITATION)]
        elif self.request.method in ['PATCH', 'PUT']:
            return [IsAuthenticated()]
        elif self.request.method in ['DELETE']:
            return [IsAuthenticated(), OrganizationPermission(Permission.DELETE_MEMBER_INVITATION)]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # Optimize query with select_related
        return OrganizationMemberInvitation.objects.filter(
            organization_id=self.kwargs['organization_pk']
        ).select_related('organization', 'invited_by')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return  CreateInviteOrganizationMemberSerializer
        elif self.request.method in ['PATCH', 'PUT']:
            return UpdateInviteOrganizationMemberSerializer
        return InvitedOrganizationMemberSerializer
    
    def perform_destroy(self, instance):
        if instance.status != OrganizationMemberInvitation.PENDING:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Only pending invitations can be deleted.")
        return super().perform_destroy(instance)
    
    
    #TODO: check if the user has the proper permission
    def perform_create(self, serializer):
        # Check if the user has the proper permission
        if not self.request.user.has_perm(Permission.CREATE_MEMBER_INVITATION, serializer.validated_data.get('organization')):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(_("You don't have permission to create member invitations."))
        
        serializer.save()
    

    def get_serializer_context(self):
        # Get the context from the parent class (including timezone)
        context = super().get_serializer_context()
        # Add your custom context
        context['organization_id'] = self.kwargs['organization_pk']
        return context
    
    
    
    
