from rest_framework import permissions 

class PersinalPagePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow GET requests as they are read-only
        if request.method in ['GET']:
            return True
        # Allow 'PATCH' requests if the user is updating their own information
        elif request.method == 'PATCH':
            return request.user.id == int(view.kwargs.get('pk'))
        return False

class IsTeamCreatorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.creator == request.user

# Permisshions for game schedule update
class IsTeamCreatorOrReadOnlyForSchedule(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow GET requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow PATCH requests for authenticated users (for voting)
        if request.method == 'PATCH':
            return request.user and request.user.is_authenticated
        # Allow POST requests for authenticated users
        if request.method == 'POST':
            return request.user and request.user.is_authenticated
        return False

    def has_object_permission(self, request, view, obj):
        # Allow GET requests for all users
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow PATCH requests for authenticated users (for voting)
        if request.method == 'PATCH':
            return True
        # Allow POST requests only for the team creators
        if request.method == 'POST':
            return obj.team_1.creator == request.user or obj.team_2.creator == request.user
        return False
