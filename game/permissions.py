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
