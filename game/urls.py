
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserPersonalPageViewSet, TeamViewSet, TeamMembershipViewSet, InvitationViewSet

router = DefaultRouter()
router.register(r'personal_page', CustomUserPersonalPageViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'team_membership', TeamMembershipViewSet)
router.register(r'invitation', InvitationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
