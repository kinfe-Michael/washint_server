# books/views.py

from rest_framework import viewsets, permissions,status
from .models import User,UserProfile
from rest_framework.decorators import action
from .serializers import UserSerializer,UserProfileSerializer
from .permissions import IsUserOrAdmin,IsOwnerOrReadOnly # Import your new permission class
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
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
    @action(detail=False, methods=['get'])
    def check_username(self,request):
        username = request.query_params.get('username',None)
        if username is None:
            return Response(
                {'message':'please provide a user name to check.'}
            )
        is_taken = User.objects.filter(username__iexact = username)
        if is_taken:
            return Response (
                {'is_avaliable':False,'message':'This username is already taken.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response (
                {'is_avaliable':True,'message':'This username is avaliable..'},
                status=status.HTTP_200_OK
            )
        
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
