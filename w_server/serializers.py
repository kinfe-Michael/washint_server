from rest_framework import serializers
from .models import (
    User, UserProfile, Artist, Album, Song, Genre, Playlist,
    PlaylistSong, Follow, UserSubscription
)

# Reusing existing serializers
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

class FullUserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']

class ManagedByUserSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.CharField(source='profile.profile_picture_url')
    class Meta:
        model = User
        fields = ['id','profile_picture_url']

class ArtistSerializer(serializers.ModelSerializer):
    managed_by = FullUserSerializer(read_only=True)
    class Meta:
        model = Artist
        fields = ['id','genre','managed_by']

class ArtistListSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='managed_by.full_name',read_only=True)
    username = serializers.CharField(source='managed_by.username',read_only=True)
    profile_picture_url = serializers.CharField(source='managed_by.profile.profile_picture_url',read_only=True)

    class Meta:
        model = Artist
        fields = ['id','genre','display_name','username','profile_picture_url']

class ArtistManagedBySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name']

class AlbumSerializer(serializers.ModelSerializer):
    artist = ArtistManagedBySerializer(source='artist.managed_by',read_only=True)
    signed_cover_art_url = serializers.SerializerMethodField(read_only=True)
    cover_art_upload = serializers.ImageField(write_only=True)
    class Meta:
        model = Album
        fields =  ['id','title','artist','cover_art_upload','signed_cover_art_url']
    def get_signed_cover_art_url(self, obj):
        if obj.cover_art_upload:
            return obj.cover_art_upload.url
        return None
    def validate(self, data):
        """
        Custom validation to check for a unique album title for a specific artist.
        """
        user = self.context['request'].user
        
        try:
            artist = Artist.objects.get(managed_by=user)
        except Artist.DoesNotExist:
            raise serializers.ValidationError({'error':"Authenticated user does not have an associated artist profile."})

        if Album.objects.filter(artist=artist, title__iexact=data['title']).exists():
            raise serializers.ValidationError(
                {'error': f"An album with the title '{data['title']}' already exists for this artist."}
            )
        
        data['artist'] = artist
        
        return data

    def create(self, validated_data):
        cover_art_file = validated_data.pop('cover_art_upload', None)
        
        album = Album.objects.create(cover_art_upload=cover_art_file, **validated_data)
        return album

class SongCreditSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)

class SongSerializer(serializers.ModelSerializer):
    audio_file_upload = serializers.FileField(write_only=True)
    song_cover_upload = serializers.ImageField(write_only=True)
    signed_audio_url = serializers.SerializerMethodField(read_only=True)
    signed_cover_url = serializers.SerializerMethodField(read_only=True)
    artist = ArtistManagedBySerializer(source='artist.managed_by',read_only=True)
    duration_seconds = serializers.ReadOnlyField()
    genres = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Genre.objects.all(),
    )
    credits = SongCreditSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Song
        fields = [
            'id', 'title', 'album', 'genres',
            'audio_file_upload', 'signed_audio_url', 'song_cover_upload','signed_cover_url','credits',
            'duration_seconds', 'artist', 'play_count', 'created_at'
        ]
        read_only_fields = ['id', 'play_count', 'created_at']
        
    def get_signed_audio_url(self, obj):
        if obj.audio_file_url:
            return obj.audio_file_url.url
        return None
    def get_signed_cover_url(self, obj):
        if obj.song_cover_upload:
            return obj.song_cover_upload.url
        return None

    def create(self, validated_data):
        audio_file = validated_data.pop('audio_file_upload')
        cover_file = validated_data.pop('song_cover_upload')
        genres_data = validated_data.pop('genres', [])
        credits_data = validated_data.pop('credits', [])
        validated_data['duration_seconds'] = 300 
        song = Song.objects.create(audio_file_url=audio_file,song_cover_upload=cover_file, **validated_data)
        if genres_data:
            song.genres.set(genres_data)
        if credits_data:
            song.credits = credits_data
            song.save()
        return song

class PlaylistListSerializer(serializers.ModelSerializer):
    """
    A serializer for listing playlists, including the owner's full details
    and a count of songs.
    """
    owner = FullUserSerializer(read_only=True)
    songs_count = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id',
            'title',
            'owner',
            'is_public',
            'songs_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at',)

    def get_songs_count(self, obj):
        return obj.songs.count()


class PlaylistDetailSerializer(serializers.ModelSerializer):
    """
    A serializer for a single playlist, including the owner's details
    and a full, nested list of songs.
    """
    songs = serializers.SerializerMethodField()
    owner = FullUserSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id',
            'title',
            'owner',
            'is_public',
            'songs',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at',)

    def get_songs(self, obj):
        """
        Manually serializes the songs in the playlist.
        This prevents the AttributeError on retrieve.
        """
        return SongSerializer(obj.songs.all(), many=True, context=self.context).data


class PlaylistCreateSerializer(serializers.ModelSerializer):
    """
    A serializer for creating and updating playlists.
    It uses PrimaryKeyRelatedField for songs.
    """
    songs = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Song.objects.all(),
        required=False,
    )
    class Meta:
        model = Playlist
        fields = ['id', 'title', 'is_public', 'songs']
        read_only_fields = ['id', 'created_at', 'updated_at']
