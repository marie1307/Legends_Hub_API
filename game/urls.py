
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, TeamViewSet, TeamMembershipViewSet

router = DefaultRouter()
router.register(r'personal_page', CustomUserViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'team_membership', TeamMembershipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
