# books/views.py

from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer
from .permissions import IsUserOrAdmin # Import your new permission class

class UserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all() # Fetch all users for admin use
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Anyone can register
            return [permissions.AllowAny()]
        
        elif self.action == 'list':
            # Only admins can see a list of all users
            return [permissions.IsAdminUser()]

        # For 'retrieve', 'update', 'partial_update', and 'destroy'
        else:
            # The user must be authenticated, and either an admin or the object owner.
            return [permissions.IsAuthenticated(), IsUserOrAdmin()]