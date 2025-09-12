from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions, status,serializers
from rest_framework.decorators import action
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UserProfile,Artist,Song,Album,Playlist,PlaylistSong,Follow
from .serializers import UserSerializer, UserProfileSerializer,ArtistSerializer,SongSerializer,AlbumSerializer,ArtistListSerializer,PlaylistListSerializer,PlaylistDetailSerializer,PlaylistCreateSerializer,AddSongToPlaylistSerializer,PlaylistSongSerializer,FollowSerializer
from .permissions import IsUserOrAdmin, IsOwnerOrReadOnly
from washint_server.pagination import MyLimitOffsetPagination 
from django.conf import settings
from django.db.models import F
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from botocore.exceptions import ClientError
from django.shortcuts import get_object_or_404
User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    A ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = MyLimitOffsetPagination # Add this line

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'check_username']:
            return [permissions.AllowAny()]
        
        elif self.action == 'list':
            return [permissions.IsAdminUser()]

        else:
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
        return Response({'profile':serializer.data})

class ArtistViewSets(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 

    def perform_create(self, serializer):
        if Artist.objects.filter(managed_by=self.request.user).exists():
            return Response(
                {"detail": "You can only manage one artist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = self.request.user
        artist_name = user.username
        
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.display_name:
                artist_name = profile.display_name
        except UserProfile.DoesNotExist:
            pass
            
        serializer.save(managed_by=user, name=artist_name)
        
    def get_queryset(self):
        user_id = self.request.query_params.get('artist_id',None)
        if user_id:
            queryset = Artist.objects.filter(managed_by__id=user_id)
        else:
            queryset = Artist.objects.filter(managed_by=self.request.user)

        return queryset
class PublicArtistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 

    def get_serializer_class(self):
        if(self.action == 'list'):
            return ArtistListSerializer
        if(self.action == 'retrieve'):
            return ArtistSerializer
        return ArtistSerializer
class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 
    
    parser_classes = (MultiPartParser, FormParser,)

    def perform_create(self, serializer):
        user = self.request.user

        try:
            artist = Artist.objects.get(managed_by=user)
        except Artist.DoesNotExist:
            raise ValidationError("Authenticated user does not have an associated artist profile.")

        serializer.save(artist=artist)

class AlbumViewSets(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        artist_id = self.request.query_params.get('artist_id', None)

        if self.request.method in permissions.SAFE_METHODS:
            if artist_id:
                return self.queryset.filter(artist__id=artist_id)
            else:
                return self.queryset.all()
        
        try:
            artist = Artist.objects.get(managed_by=self.request.user)
            return self.queryset.filter(artist=artist)
        except Artist.DoesNotExist:
            return self.queryset.none()
class AlbumSongViewSets(viewsets.ReadOnlyModelViewSet):
    """
    A nested ViewSet for listing songs within a specific album.
    """
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 

    def get_queryset(self):
        album_pk = self.kwargs.get('album_pk')
        
        album = get_object_or_404(Album, id=album_pk)

        return album.songs.all()

class PlayListViewSets(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 
    def get_serializer_class(self):
       
        if self.action == 'list':
            return PlaylistListSerializer
        elif self.action == 'create':
            return PlaylistCreateSerializer
        return PlaylistDetailSerializer

    def get_queryset(self):
       
        queryset = Playlist.objects.filter(is_public=True)
        
        user = self.request.user
        
        if self.request.query_params.get('my-playlists') == 'true' and user.is_authenticated:
            return Playlist.objects.filter(owner=user).order_by('created_at').distinct()
        
        if user.is_authenticated:
            queryset = queryset | Playlist.objects.filter(is_public=False, owner=user)
        
        return queryset.order_by('created_at').distinct()
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
class PlaylistSongViewSet(viewsets.ViewSet):
    """
    A ViewSet for managing songs in a playlist.
    """
    def get_playlist(self):
        playlist_id = self.kwargs.get('playlist_pk')
        return get_object_or_404(Playlist, id=playlist_id)

    @action(detail=False, methods=['post'], url_path='add-song')
    def add_song(self, request, playlist_pk=None):
        """
        Add a song to a specific playlist.
        """
        playlist = self.get_playlist()
        serializer = AddSongToPlaylistSerializer(data=request.data, context={'playlist': playlist})
        serializer.is_valid(raise_exception=True)
        playlist_song = serializer.save()
        return Response(PlaylistSongSerializer(playlist_song).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path='remove-song/(?P<song_pk>[^/.]+)')
    def remove_song(self, request, playlist_pk=None, song_pk=None):
        """
        Remove a song from a specific playlist.
        """
        playlist = self.get_playlist()
        
        try:
            playlist_song = PlaylistSong.objects.get(playlist=playlist, song__id=song_pk)
            playlist_song.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PlaylistSong.DoesNotExist:
            return Response({"detail": "Song not found in the playlist."}, status=status.HTTP_404_NOT_FOUND)

    
class ArtistSongViewSets(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsOwnerOrReadOnly]
    pagination_class = MyLimitOffsetPagination 

    def get_queryset(self):
        artist_id = self.kwargs.get('artist_pk')
        artist = get_object_or_404(Artist, id=artist_id)
        return artist.songs.all()
class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        follow_instance = serializer.save(follower=self.request.user)
        
        follower_profile = UserProfile.objects.get(user=follow_instance.follower)
        following_profile = UserProfile.objects.get(user=follow_instance.following)

        UserProfile.objects.filter(id=follower_profile.id).update(following_count=F('following_count') + 1)
        UserProfile.objects.filter(id=following_profile.id).update(followers_count=F('followers_count') + 1)
    
    def perform_destroy(self, instance):
        follower = instance.follower
        following = instance.following
        
        try:
            UserProfile.objects.filter(user=follower).update(following_count=F('following_count') - 1)
            UserProfile.objects.filter(user=following).update(followers_count=F('followers_count') - 1)
        except UserProfile.DoesNotExist:
            pass
            
        instance.delete()
        
    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_followers(self, request):
        """
        Returns a list of UserProfile objects for the users who are following me.
        """
        followers_profiles = UserProfile.objects.filter(
            user__following__following=request.user
        )
        serializer = UserProfileSerializer(followers_profiles, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_following(self, request):
        """
        Returns a list of UserProfile objects for the users I am following.
        """
        following_profiles = UserProfile.objects.filter(
            user__followers__follower=request.user
        )
        serializer = UserProfileSerializer(following_profiles, many=True, context={'request': request})
        return Response(serializer.data)
    @action(detail=False, methods=['get'], url_path='is-following')
    def is_following(self, request):
        """
        Checks if the current user is following the user specified by `user_id` query param.
        Example: /api/follows/is-following/?user_id=<uuid>
        """
        target_user_id = request.query_params.get('user_id')
        
        if not target_user_id:
            return Response({"detail": "User ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        is_following = Follow.objects.filter(
            follower=request.user,
            following_id=target_user_id
        ).exists()

        return Response({"is_following": is_following})

@api_view(['GET'])
def search(request):
    """
    Performs a full-text search across songs, artists, and albums using weighted ranking.
    The query is provided via the 'q' query parameter.
    """
    query_string = request.GET.get('q', '')

    if not query_string:
        return JsonResponse({"results": []})

    query = SearchQuery(query_string)

    weights = [1.0, 0.8, 0.6, 0.4]

    songs_queryset = Song.objects.annotate(
        search_vector=SearchVector(
            'title', weight='A', config='english'
        ) + SearchVector(
            'album__title', weight='B', config='english'
        ) + SearchVector(
            'artist__name', weight='C', config='english'
        )
    ).filter(search_vector=query)

    songs_results = []
    for song in songs_queryset.annotate(rank=SearchRank(F('search_vector'), query, weights=weights)).order_by('-rank')[:20]:
        serializer = SongSerializer(song, context={'request': request})
        songs_results.append(serializer.data)

    artists_queryset = Artist.objects.annotate(
        search_vector=SearchVector('name', weight='A', config='english')
    ).filter(search_vector=query)

    artists_results = []
    for artist in artists_queryset.annotate(rank=SearchRank(F('search_vector'), query, weights=weights)).order_by('-rank')[:20]:
        profile = getattr(artist.managed_by, 'profile', None)
        signed_profile_url = profile.profile_picture_url.url if profile and profile.profile_picture_url else None
        artists_results.append({
            'id': artist.id,
            'name': artist.name,
            'rank': artist.rank,
            'signed_profile_url': signed_profile_url,
        })

    albums_queryset = Album.objects.annotate(
        search_vector=SearchVector('title', weight='A', config='english') + SearchVector('artist__name', weight='B', config='english')
    ).filter(search_vector=query)
    
    albums_results = []
    for album in albums_queryset.annotate(rank=SearchRank(F('search_vector'), query, weights=weights)).order_by('-rank')[:20]:
        albums_results.append({
            'id': album.id,
            'title': album.title,
            'artist_name': album.artist.name,
            'rank': album.rank,
            'signed_cover_art_url': album.cover_art_upload.url if album.cover_art_upload else None
        })

    results = {
        'songs': songs_results,
        'artists': artists_results,
        'albums': albums_results
    }

    return JsonResponse(results)