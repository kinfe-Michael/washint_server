# books/permissions.py

from rest_framework import permissions

class IsUserOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow a user to perform actions on their own object,
    or allow an admin user to perform any action.
    """
    def has_object_permission(self, request, view, obj):
        # Allow read permissions (GET, HEAD, OPTIONS) for any authenticated user.
        # This is for public profile viewing.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if the user is an admin, they have full access.
        if request.user and request.user.is_staff:
            return True
        
        # Check if the user trying to modify the object is the same as the object owner.
        return obj == request.user