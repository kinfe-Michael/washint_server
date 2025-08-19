
from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import UserProfile,Artist
from .serializers import UserSerializer, UserProfileSerializer,ArtistSerializer
from .permissions import IsUserOrAdmin, IsOwnerOrReadOnly

# CRITICAL FIX: Use get_user_model() to retrieve the active user model.
User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        # CRITICAL FIX: Handle the 'check_username' action specifically here.
        if self.action in ['create', 'check_username']:
            # Anyone can register or check a username.
            return [permissions.AllowAny()]
        
        elif self.action == 'list':
            # Only admins can see a list of all users.
            return [permissions.IsAdminUser()]

        else:
            # For 'retrieve', 'update', 'partial_update', and 'destroy',
            # the user must be authenticated, and either an admin or the object owner.
            return [permissions.IsAuthenticated(), IsUserOrAdmin()]
        
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def check_username(self, request):
        """
        Check if a username is already taken.
        Usage: /api/users/check_username/?username=newuser
        """
        username = request.query_params.get('username', None)
        if username is None:
            return Response(
                {'message': 'Please provide a username to check.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        is_taken = User.objects.filter(username__iexact=username).exists()
        if is_taken:
            return Response (
                {'is_available': False, 'message': 'This username is already taken.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response (
                {'is_available': True, 'message': 'This username is available.'},
                status=status.HTTP_200_OK
            )
        
class UserProfileViewSets(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        if UserProfile.objects.filter(user=self.request.user).exists():
            raise ValidationError("A profile for this user already exists.")
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.all()
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=False,methods=['get'],url_path='my-profile')
    def my_profile(self,request):
        isNew = False
        if not request.user.is_authenticated:
            return Response(
                {'detail':'authentication credentials was not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=user)
            isNew:True
        serializer = self.get_serializer(profile)
        return Response({'profile':serializer.data,'isNew':isNew})
    @action(detail=False,methods=['get'],permission_classes=[AllowAny])
    def user_profile(self,request):
        username = request.query_params.get('username',None)
        if username is None:
            return Response({'error':{'message':'sername not provided'}},status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.get(username = username)
        serializer = self.get_serializer(user.profile)
        # profileData = User.objects.filter(user = userData)
        # if not profileData: 
            # return Response({'error':{'message':'user not found'}},status=status.HTTP_400_BAD_REQUEST)
        return Response({'profile':serializer.data})

class ArtistViewSets(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    def perform_create(self, serializer):
        if Artist.objects.filter(managed_by=self.request.user).exists():
            return Response(
                {"detail": "You can only manage one artist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer.save(managed_by=self.request.user)
    def get_queryset(self):
        user_id = self.request.query_params.get('artist_id',None)
        if user_id:
            queryset = Artist.objects.filter(managed_by__id=user_id)
        else:
            queryset = Artist.objects.filter(managed_by=self.request.user)

        return queryset
