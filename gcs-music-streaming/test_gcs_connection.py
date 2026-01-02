"""
Test GCS connection and verify bucket access
"""

import os
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


def test_gcs_connection():
    """
    Test GCS connection and list available files
    """
    bucket_name = os.getenv('GCS_BUCKET_NAME')
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    print("\n" + "="*60)
    print("GCS Connection Test")
    print("="*60 + "\n")

    # Check environment variables
    print("1. Checking environment variables...")
    if not bucket_name:
        print("   ❌ GCS_BUCKET_NAME not set")
        return False
    print(f"   ✅ Bucket name: {bucket_name}")

    if not credentials_path:
        print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    print(f"   ✅ Credentials path: {credentials_path}")

    # Check credentials file
    print("\n2. Checking credentials file...")
    if not os.path.exists(credentials_path):
        print(f"   ❌ File not found: {credentials_path}")
        return False
    print(f"   ✅ File exists: {credentials_path}")

    # Try to connect
    print("\n3. Connecting to GCS...")
    try:
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(bucket_name)
        bucket.reload()  # Test bucket access
        print(f"   ✅ Successfully connected to bucket: {bucket_name}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

    # List files
    print("\n4. Listing files in bucket...")
    try:
        blobs = bucket.list_blobs(max_results=10)
        files = list(blobs)

        if not files:
            print("   ⚠️  No files found in bucket")
        else:
            print(f"   ✅ Found files (showing first 10):")
            for blob in files:
                print(f"      - {blob.name}")

    except Exception as e:
        print(f"   ❌ Failed to list files: {e}")
        return False

    # Test signed URL generation
    print("\n5. Testing signed URL generation...")
    try:
        if files:
            test_blob = files[0]
            url = test_blob.generate_signed_url(
                version='v4',
                expiration=3600,
                method='GET'
            )
            print(f"   ✅ Generated signed URL for: {test_blob.name}")
            print(f"      URL (truncated): {url[:80]}...")
        else:
            print("   ⚠️  No files to test with")

    except Exception as e:
        print(f"   ❌ Failed to generate signed URL: {e}")
        return False

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60 + "\n")
    return True


if __name__ == '__main__':
    success = test_gcs_connection()
    if success:
        print("You can now run the service: python music_service_gcs.py\n")
    else:
        print("Please fix the issues above before running the service.\n")
