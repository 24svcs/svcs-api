from django.urls import path, include
from rest_framework_nested import routers
from org.views import OrganizationViewSet , OrganizationMemberInvitationViewSet, OrganizationMemberViewSet, MyOrganizationViewSet
from hr.views import DepartmentModelViewset, PositionModelViewset, EmployeeModelViewset, AttendanceModelViewset
from . views import send_email


router = routers.DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organizations')

router.register('my-organization', MyOrganizationViewSet, basename='my_organization')

member_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
member_router.register(r'members', OrganizationMemberViewSet, basename='member')

invitation_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
invitation_router.register(r'invitations', OrganizationMemberInvitationViewSet, basename='invitation')


department_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
department_router.register(r'departments', DepartmentModelViewset, basename='department')


position_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
position_router.register(r'positions', PositionModelViewset, basename='position')


employee_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
employee_router.register(r'employees', EmployeeModelViewset, basename='employee')


attendance_router = routers.NestedDefaultRouter(router, r'organizations', lookup='organization')
attendance_router.register(r'attendances', AttendanceModelViewset, basename='attendance')


urlpatterns = [
     path(r'', include(router.urls)),
     path(r'', include(member_router.urls)),
     path(r'', include(invitation_router.urls)),
     path('send-email/', send_email, name='send-email'),
     path(r'', include(department_router.urls)),
     path(r'', include(position_router.urls)),
     path(r'', include(employee_router.urls)),
     path(r'', include(attendance_router.urls)),
]