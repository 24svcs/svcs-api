
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission
from api.pagination import CustomPagination
from core.serializers import PermissionSerializer
import pytz


def health_check(request):
    return Response({"status": "ok"}, status=status.HTTP_200_OK)


    
class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = CustomPagination
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    @api_view(['PUT'])
    @permission_classes([IsAuthenticated])
    def update_user_timezone(request):
        """
        Update the authenticated user's timezone preference
        """
        timezone_str = request.data.get('timezone')
        
        if not timezone_str:
            return Response(
                {"error": "Timezone is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate the timezone
        try:
            pytz.timezone(timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            return Response(
                {"error": f"Invalid timezone: {timezone_str}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the user's timezone
        request.user.timezone = timezone_str
        request.user.save()
        
        return Response({"timezone": timezone_str}, status=status.HTTP_200_OK)