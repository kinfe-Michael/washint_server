# books/views.py

from rest_framework import viewsets, permissions
from .models import User,UserProfile
from .serializers import UserSerializer,UserProfileSerializer
from .permissions import IsUserOrAdmin,IsOwnerOrReadOnly # Import your new permission class
from rest_framework.exceptions import ValidationError
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
        
class UserProfileViewSets(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    def perform_create(self, serializer):
        if UserProfile.objects.filter(user = self.request.user).exists():
            raise ValidationError("a profile for this user already exists.")
        serializer.save(user=self.request.user)
    def get_queryset(self):
        return self.queryset.all()