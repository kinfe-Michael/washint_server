# your_app/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First, try to get the token from the Authorization header (standard behavior)
        header = self.get_header(request)
        if header:
            return super().authenticate(request)

        # If no Authorization header, check for the token in a cookie
        raw_token = request.COOKIES.get('access_token')  # Or whatever you named your cookie
        if raw_token is None:
            return None

        # Authenticate the token from the cookie
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token