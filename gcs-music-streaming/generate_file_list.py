"""
Generate GCS music file list cache
Run this script after uploading new files to your GCS bucket
"""

import os
import json
import logging
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_file_list():
    """
    Fetch all MP3 files from GCS bucket and save to JSON cache
    """
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    output_file = 'gcs_music_files.json'

    if not bucket_name:
        logger.error("GCS_BUCKET_NAME not found in environment variables")
        return False

    if not credentials_path or not os.path.exists(credentials_path):
        logger.error(f"GCS credentials file not found: {credentials_path}")
        return False

    try:
        # Initialize GCS client
        logger.info(f"Connecting to GCS bucket: {bucket_name}")
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(bucket_name)

        # Fetch all blobs
        logger.info("Fetching file list from GCS...")
        blobs = bucket.list_blobs()

        # Filter MP3 files
        mp3_files = []
        folder_counts = {}

        for blob in blobs:
            if blob.name.lower().endswith('.mp3'):
                mp3_files.append(blob.name)

                # Count files per folder
                if '/' in blob.name:
                    folder = blob.name.split('/')[0]
                    folder_counts[folder] = folder_counts.get(folder, 0) + 1

        # Sort files
        mp3_files.sort()

        # Save to JSON
        logger.info(f"Saving {len(mp3_files)} files to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mp3_files, f, indent=2, ensure_ascii=False)

        # Print summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Successfully generated file list cache!")
        logger.info(f"{'='*60}")
        logger.info(f"Total MP3 files: {len(mp3_files)}")
        logger.info(f"Output file: {output_file}")
        logger.info(f"\nFiles per folder:")
        for folder, count in sorted(folder_counts.items()):
            logger.info(f"  {folder}: {count} files")
        logger.info(f"{'='*60}\n")

        return True

    except Exception as e:
        logger.error(f"Failed to generate file list: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    success = generate_file_list()
    if success:
        print("\n✅ File list cache generated successfully!")
        print("You can now run: python music_service_gcs.py")
    else:
        print("\n❌ Failed to generate file list cache")
        print("Please check your GCS credentials and bucket name")
