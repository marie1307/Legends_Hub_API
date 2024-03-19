
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserPersonalPageViewSet, TeamViewSet, InvitationViewSet, NotificationViewSet, TeamsListViewSet, UsersListViewSet

router = DefaultRouter()
router.register(r'personal_page', CustomUserPersonalPageViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'invitation', InvitationViewSet)
router.register(r'notification', NotificationViewSet)
router.register(r'teams_list', TeamsListViewSet, basename="teams_list")
router.register(r'users_list', UsersListViewSet, basename="users_list")


urlpatterns = [
    path('', include(router.urls)),
]
