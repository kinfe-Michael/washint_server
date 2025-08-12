# myproject/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView, # Optional: For verifying tokens
)

# Import your ViewSet from its location
from w_server.views import UserViewSet,UserProfileViewSets

# Create a router instance
router = DefaultRouter()

# Register the ViewSet with a URL prefix.
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles',UserProfileViewSets,basename='profile')

urlpatterns = [
    path('admin/', admin.site.urls),

    # THIS IS THE CRITICAL LINE:
    # It tells Django to include all the router's URLs under the 'api/' path.
    path('api/', include(router.urls)),

    # This is for the browsable API's login/logout, which is a good practice to include.
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]