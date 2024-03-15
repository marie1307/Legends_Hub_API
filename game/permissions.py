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



    # def has_permission(self, request, view):
    #     # Only authenticates users can send POST request
    #     if request.method == 'POST':
    #         return request.user.is_authenticated

    #     return True

    # def has_object_permission(self, request, view, obj):
    #     user = request.user
    #     print(obj)
    #     # Admins can everything
    #     if user.role == 'administrator':
    #         return True

    #     # Only owners can add SUBMIT status
    #     if user.role == 'owner':
    #         if request.method in permissions.SAFE_METHODS:
    #             return True  # Allows read-only actions
    #         return obj.user == user and obj.status == 'pending'

    #     # Disrupts access for everyone
    #     return False
