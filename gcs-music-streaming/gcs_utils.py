"""
Google Cloud Storage Utilities for Music Streaming
"""

import os
import json
import logging
from datetime import timedelta
from google.cloud import storage
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class GCSMusicManager:
    """
    Manages music file operations with Google Cloud Storage
    """

    def __init__(self, bucket_name=None, credentials_path=None, cache_file='gcs_music_files.json'):
        """
        Initialize GCS Music Manager

        Args:
            bucket_name: GCS bucket name
            credentials_path: Path to service account key JSON file
            cache_file: Path to cached file list JSON
        """
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.cache_file = cache_file
        self.storage_client = None
        self.bucket = None
        self.all_files = []

        # Initialize GCS client
        self._init_gcs_client()

        # Load file list (from cache or GCS)
        self._load_file_list()

    def _init_gcs_client(self):
        """
        Initialize Google Cloud Storage client
        """
        try:
            if not self.credentials_path or not os.path.exists(self.credentials_path):
                logger.error(f"GCS credentials file not found: {self.credentials_path}")
                return

            # Create credentials from service account key
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )

            # Initialize storage client
            self.storage_client = storage.Client(credentials=credentials)
            self.bucket = self.storage_client.bucket(self.bucket_name)

            logger.info(f"GCS client initialized for bucket: {self.bucket_name}")

        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.storage_client = None
            self.bucket = None

    def _load_file_list(self):
        """
        Load file list from cache or fetch from GCS
        """
        # Try loading from cache first
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.all_files = json.load(f)
                logger.info(f"Loaded {len(self.all_files)} files from cache: {self.cache_file}")
                return
            except Exception as e:
                logger.warning(f"Failed to load cache file: {e}")

        # If cache not available, fetch from GCS
        self._refresh_file_list()

    def _refresh_file_list(self):
        """
        Fetch all MP3 files from GCS bucket and update cache
        """
        if not self.bucket:
            logger.error("GCS bucket not initialized, cannot refresh file list")
            return

        try:
            logger.info(f"Fetching file list from GCS bucket: {self.bucket_name}")
            blobs = self.bucket.list_blobs()

            self.all_files = []
            for blob in blobs:
                # Only include MP3 files
                if blob.name.lower().endswith('.mp3'):
                    self.all_files.append(blob.name)

            logger.info(f"Fetched {len(self.all_files)} MP3 files from GCS")

            # Save to cache
            self._save_cache()

        except Exception as e:
            logger.error(f"Failed to refresh file list from GCS: {e}")

    def _save_cache(self):
        """
        Save file list to cache
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_files, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.all_files)} files to cache: {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save cache file: {e}")

    def get_files_from_folders(self, folder_list):
        """
        Get all files from specified folders

        Args:
            folder_list: List of folder names (e.g., ['Fantasy_mp3', 'World_mp3'])

        Returns:
            List of file paths matching the folders
        """
        matching_files = []

        for file_path in self.all_files:
            # Check if file is in any of the specified folders
            for folder in folder_list:
                if file_path.startswith(folder + '/'):
                    matching_files.append(file_path)
                    break

        logger.info(f"Found {len(matching_files)} files in folders: {folder_list}")
        return matching_files

    def generate_signed_url(self, blob_name, expiration_minutes=60):
        """
        Generate a signed URL for streaming a file from GCS

        Args:
            blob_name: Path to file in GCS bucket (e.g., 'Fantasy_mp3/Song.mp3')
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string
        """
        if not self.bucket:
            logger.error("GCS bucket not initialized, cannot generate signed URL")
            return None

        try:
            blob = self.bucket.blob(blob_name)

            # Generate signed URL
            url = blob.generate_signed_url(
                version='v4',
                expiration=timedelta(minutes=expiration_minutes),
                method='GET'
            )

            logger.info(f"Generated signed URL for {blob_name} (expires in {expiration_minutes} min)")
            return url

        except Exception as e:
            logger.error(f"Failed to generate signed URL for {blob_name}: {e}")
            return None

    def verify_connection(self):
        """
        Verify GCS connection by checking bucket access

        Returns:
            True if connection is successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCS bucket not initialized")
            return False

        try:
            # Try to access bucket metadata
            self.bucket.reload()
            logger.info(f"Successfully connected to GCS bucket: {self.bucket_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify GCS connection: {e}")
            return False

    def get_file_count(self):
        """
        Get total number of music files

        Returns:
            Number of files
        """
        return len(self.all_files)

    def get_folders(self):
        """
        Get list of all unique folders in the bucket

        Returns:
            List of folder names
        """
        folders = set()
        for file_path in self.all_files:
            if '/' in file_path:
                folder = file_path.split('/')[0]
                folders.add(folder)

        return sorted(list(folders))

    def refresh(self):
        """
        Manually refresh file list from GCS
        """
        self._refresh_file_list()

    def upload_file(self, local_path, destination_blob_name):
        """
        Upload a file to GCS bucket

        Args:
            local_path: Local file path
            destination_blob_name: Destination path in GCS (e.g., 'Fantasy_mp3/song.mp3')

        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCS bucket not initialized")
            return False

        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_path)
            logger.info(f"Uploaded {local_path} to {destination_blob_name}")

            # Add to file list and refresh cache
            if destination_blob_name.lower().endswith('.mp3'):
                self.all_files.append(destination_blob_name)
                self._save_cache()

            return True

        except Exception as e:
            logger.error(f"Failed to upload {local_path}: {e}")
            return False

    def delete_file(self, blob_name):
        """
        Delete a file from GCS bucket

        Args:
            blob_name: Path to file in GCS bucket

        Returns:
            True if successful, False otherwise
        """
        if not self.bucket:
            logger.error("GCS bucket not initialized")
            return False

        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Deleted {blob_name} from GCS")

            # Remove from file list and refresh cache
            if blob_name in self.all_files:
                self.all_files.remove(blob_name)
                self._save_cache()

            return True

        except Exception as e:
            logger.error(f"Failed to delete {blob_name}: {e}")
            return False
