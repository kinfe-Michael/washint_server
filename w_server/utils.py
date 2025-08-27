# your_app_name/utils.py

from mutagen import File as MutagenFile
from io import BytesIO

def get_audio_duration(audio_file):
    """
    Calculates the duration of an audio file in seconds using mutagen.
    
    Args:
        audio_file: A Django uploaded file object (e.g., from request.FILES).
    
    Returns:
        float: The duration of the audio in seconds, or None if the duration cannot be determined.
    """
    try:
        # Mutagen can read from a file-like object, which the uploaded file is.
        # We need to seek to the beginning of the file to ensure Mutagen can read it.
        audio_file.seek(0)
        
        # Use a BytesIO wrapper for better compatibility with Mutagen
        file_buffer = BytesIO(audio_file.read())
        
        audio = MutagenFile(file_buffer)
        
        if audio and hasattr(audio.info, 'length'):
            return audio.info.length
        
    except Exception as e:
        # Log the error for debugging, but don't crash the application
        print(f"Error calculating audio duration: {e}")
        return None
    finally:
        # Seek back to the beginning of the file for the next process (e.g., saving)
        audio_file.seek(0)