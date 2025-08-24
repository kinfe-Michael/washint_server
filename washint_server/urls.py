# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView, 
)

from w_server.views import UserViewSet,UserProfileViewSets,ArtistViewSets,PublicArtistViewSet,SongViewSet

router = DefaultRouter()

router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles',UserProfileViewSets,basename='profile')
router.register(r'artists',ArtistViewSets,basename='artist')
router.register(r'public-artists', PublicArtistViewSet, basename='public-artist')
router.register(r'songs', SongViewSet, basename='song')
urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]