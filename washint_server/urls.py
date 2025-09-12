
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView, 
)
from rest_framework_nested import routers

from w_server import views
from w_server.views import (
    UserViewSet, UserProfileViewSets, ArtistViewSets, PublicArtistViewSet,
    SongViewSet, AlbumViewSets, PlayListViewSets, PlaylistSongViewSet,
    AlbumSongViewSets, ArtistSongViewSets ,FollowViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles',UserProfileViewSets,basename='profile')
router.register(r'artists',ArtistViewSets,basename='artist')
router.register(r'public-artists', PublicArtistViewSet, basename='public-artist')
router.register(r'songs', SongViewSet, basename='song')
router.register(r'albums',AlbumViewSets , basename='album')
router.register(r'playlists',PlayListViewSets , basename='playlist')
router.register(r'follows', FollowViewSet, basename='follow')
playlists_router = routers.NestedSimpleRouter(router, r'playlists', lookup='playlist')
playlists_router.register(r'songs', PlaylistSongViewSet, basename='playlist-songs')

album_router = routers.NestedSimpleRouter(router, r'albums', lookup='album')
album_router.register(r'songs', AlbumSongViewSets, basename='album-songs')

artists_router = routers.NestedSimpleRouter(router, r'artists', lookup='artist')
artists_router.register(r'songs', ArtistSongViewSets, basename='artist-songs')

api_url_patterns = router.urls + playlists_router.urls + album_router.urls + artists_router.urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/search/', views.search, name='api-search'),
    path('api/', include(api_url_patterns)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]