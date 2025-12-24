# GCS Music Streaming Service

AI-powered music recommendation service with Google Cloud Storage streaming. Analyzes scene descriptions using GPT-3.5 and recommends appropriate background music from a curated library stored in GCS.

## Features

- 🎵 **AI-Powered Analysis**: GPT-3.5 analyzes scene descriptions to determine mood
- ☁️ **Cloud Streaming**: Direct music streaming from Google Cloud Storage with Signed URLs
- 🎭 **19 Mood Categories**: From peaceful to epic, horror to comedy
- 🎼 **273 Music Files**: Curated library from FreePD across 16 genre folders
- 🔒 **Secure Access**: 60-minute expiring signed URLs for security
- 🌐 **REST API**: Simple JSON API for easy integration

## Architecture

```
Client Request → GPT-3.5 Analysis → Mood Extraction → File Selection → Signed URL Generation → Response
                                                                              ↓
                                                               GCS Streaming (60min URL)
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Google Cloud Platform account
- GCS bucket with music files
- OpenAI API key

### 2. Installation

```bash
# Clone or create the project
cd gcs-music-streaming

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. GCS Setup

1. **Create GCS Bucket**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new bucket (e.g., `your-music-bucket`)
   - Upload music files organized in folders

2. **Create Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create new service account
   - Grant roles: `Storage Object Viewer`, `Storage Object Creator`
   - Create JSON key and download

3. **Folder Structure in GCS**:
   ```
   your-bucket/
   ├── Fantasy_mp3/
   │   ├── Song1.mp3
   │   └── Song2.mp3
   ├── Horror_mp3/
   ├── Epic_Dramatic_mp3/
   └── ...
   ```

### 4. Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxx
   GCS_BUCKET_NAME=your-music-bucket
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\gcs-service-account-key.json
   ```

### 5. Generate File List Cache

```bash
python generate_file_list.py
```

This creates `gcs_music_files.json` with all MP3 files from your bucket.

### 6. Run the Service

```bash
python music_service_gcs.py
```

Server starts at `http://localhost:5001`

### 7. Test in Browser

Open `music_test_client.html` in your browser or visit `http://localhost:5001`

## API Endpoints

### POST /api/analyze

Analyze scene and get music recommendation.

**Request:**
```json
{
  "prompt": "주인공이 숲 속을 탐험하며 여관을 찾아 나선다"
}
```

**Response:**
```json
{
  "analysis": {
    "primary_mood": "exploration",
    "secondary_mood": "peaceful",
    "intensity": 0.65,
    "emotional_tags": ["curiosity", "adventure"],
    "reasoning": "Character exploring forest seeking inn"
  },
  "music": {
    "mood": "exploration",
    "filename": "Forest Night.mp3",
    "file_path": "Fantasy_mp3/Forest Night.mp3",
    "streaming_url": "https://storage.googleapis.com/bucket/..."
  }
}
```

### GET /api/moods

List all available moods and their mapped folders.

**Response:**
```json
{
  "peaceful": {
    "keywords": ["평화", "평온", "고요"],
    "folders": ["Miscellaneous_Chill_mp3", "Miscellaneous_Classical_mp3"]
  },
  ...
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0-GCS",
  "gcs_bucket": "your-bucket-name",
  "total_files": 273
}
```

## Supported Moods

| Mood | Korean Keywords | Example Folders |
|------|----------------|-----------------|
| peaceful | 평화, 평온, 고요 | Miscellaneous_Chill_mp3 |
| romantic | 로맨틱, 사랑 | romantic, Romantic_Sentimental_mp3 |
| mysterious | 신비, 미스터리, 호기심 | Underscoring_mp3 |
| suspense | 긴장, 스릴 | Underscoring_mp3, Epic_Dramatic_mp3 |
| horror | 공포, 무서운, 두려움 | Horror_mp3 |
| action | 액션, 전투 | Epic_Dramatic_mp3 |
| fantasy | 판타지, 마법 | Fantasy_mp3, World_mp3 |
| epic | 웅장, 장엄 | Epic_Dramatic_mp3 |
| comedy | 코미디, 유쾌한 | Comedy_mp3 |
| uplifting | 신나는, 활기찬 | Uplifting_mp3 |
| sad | 슬픈, 우울 | Romantic_Sentimental_mp3 |
| exploration | 탐험, 모험 | Fantasy_mp3, World_mp3 |
| dramatic | 드라마틱, 극적 | Epic_Dramatic_mp3 |
| tension | 긴장감, 팽팽한 | Underscoring_mp3 |
| wonder | 경이, 놀라운 | Fantasy_mp3 |
| curious | 호기심, 궁금한 | Underscoring_mp3 |
| isolation | 고립, 외로운 | Underscoring_mp3 |
| nostalgic | 향수, 그리운 | Miscellaneous_Classical_mp3 |
| dark_comedy | 블랙코미디 | Comedy_mp3 |

## Testing

### Test GCS Connection

```bash
python test_gcs_connection.py
```

### Test API

```bash
# Using curl
curl -X POST http://localhost:5001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"prompt": "주인공이 숲 속을 탐험한다"}'

# Check health
curl http://localhost:5001/api/health

# List moods
curl http://localhost:5001/api/moods
```

### Browser Test

1. Open `music_test_client.html` in browser
2. Enter scene description or click example prompts
3. Click "음악 추천 받기" button
4. Verify music plays and "✓ GCS 직접 스트리밍" badge appears

## Project Structure

```
gcs-music-streaming/
├── music_service_gcs.py      # Main Flask service
├── gcs_utils.py               # GCS utility functions
├── music_test_client.html     # Browser test client
├── generate_file_list.py      # GCS file list generator
├── test_gcs_connection.py     # GCS connection test
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── gcs_music_files.json      # Cached file list (generated)
└── README.md                 # This file
```

## Key Technical Details

### Signed URLs

- **Expiration**: 60 minutes (configurable in `gcs_utils.py`)
- **Method**: Google Cloud Storage v4 signing
- **Format**: `https://storage.googleapis.com/bucket/path?X-Goog-Algorithm=...`

### File Caching

The service caches the GCS file list in `gcs_music_files.json` to reduce API calls:
- Generated once at startup or manually via `generate_file_list.py`
- Refresh after uploading new files to GCS
- Falls back to live GCS query if cache is missing

### Mood Detection

GPT-3.5 analyzes Korean text with emotion-aware prompting:
- **Prevents misclassification**: "호기심" → mysterious (NOT horror)
- **Post-processing**: Keyword-based correction for edge cases
- **Fallback**: Defaults to "peaceful" on errors

## Troubleshooting

### "GCS client creation failed"

- Verify `gcs-service-account-key.json` exists at specified path
- Check `GOOGLE_APPLICATION_CREDENTIALS` in `.env`
- Ensure service account has `Storage Object Viewer` role

### "No module named 'google.cloud'"

```bash
pip install google-cloud-storage
```

### "ModuleNotFoundError: No module named 'openai'"

```bash
pip install openai
```

### Music doesn't play in browser

- Check browser console for CORS errors
- Verify signed URL is being generated (check response in DevTools)
- Ensure GCS bucket has public read or signed URL access enabled

### "No files found for mood"

- Run `python generate_file_list.py` to refresh cache
- Verify music files are in correct GCS folders
- Check `MUSIC_LIBRARY` mapping in `music_service_gcs.py`

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-xxxxx` |
| `GCS_BUCKET_NAME` | GCS bucket name | `my-music-bucket` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key path | `C:\keys\gcs-key.json` |
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Debug mode | `True` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5001` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |

### Adjustable Parameters

**In `gcs_utils.py`:**
- `expiration_minutes`: Signed URL expiration time (default: 60)

**In `music_service_gcs.py`:**
- `MUSIC_LIBRARY`: Add/modify mood mappings and folders
- `temperature`: GPT creativity (default: 0.7)

## Security Notes

- **Never commit** `.env` or service account JSON files to git
- **Use `.gitignore`** to exclude sensitive files
- **Signed URLs expire** after 60 minutes by default
- **CORS** is set to `*` for development - restrict in production

## License

This project uses FreePD music library (public domain).

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all environment variables are set correctly
3. Check GCS bucket permissions and file structure
4. Review server logs for detailed error messages
