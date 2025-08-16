from rest_framework import serializers
from .models import User,UserProfile

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model=User
        fields = ['id','username','email','first_name','last_name','is_active','password']
        read_only_fields = ['id','is_active']

    def create(self,validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user
    def update(self,instance,validated_data):
        password = validated_data.pop('password',None)
        user = super().update(instance,validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username',read_only=True)
    display_name = serializers.CharField(source='user.full_name',read_only=True)
    class Meta:
        model = UserProfile
        fields = [
              'id', 'username', 'display_name', 'profile_picture_url',
            'bio', 'followers_count', 'following_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'followers_count', 'following_count', 'created_at', 'updated_at']
