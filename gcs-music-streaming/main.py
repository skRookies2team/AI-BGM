"""
FastAPI Music Streaming Service
AI-powered music recommendation with Google Cloud Storage streaming

Improvements:
- GPT response caching
- Music duplicate prevention
- GPT API retry mechanism
- Signed URL caching
- Mood similarity fallback
"""

import os
import json
import logging
import random
import hashlib
import time
from typing import Dict, List, Optional, Deque
from collections import deque
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI
from dotenv import load_dotenv

from gcs_utils import GCSMusicManager
from models import (
    AnalyzeRequest,
    AnalyzeResponse,
    MusicAnalysis,
    MusicInfo,
    MoodInfo,
    HealthResponse,
    ErrorResponse
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GCS Music Streaming Service",
    description="AI-powered music recommendation with Google Cloud Storage streaming",
    version="3.1-Enhanced"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize GCS Manager
gcs_manager = GCSMusicManager(
    bucket_name=os.getenv('GCS_BUCKET_NAME'),
    credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
)

# Music Library - Maps moods to genre folders and keywords
MUSIC_LIBRARY = {
    'peaceful': {
        'keywords': ['평화', '평온', '고요', '잔잔', '평화로운', '차분한'],
        'folders': ['Miscellaneous_Chill_mp3', 'Miscellaneous_Classical_mp3']
    },
    'romantic': {
        'keywords': ['로맨틱', '사랑', '로맨스', '달콤한', '감성적', '낭만적'],
        'folders': ['romantic', 'Romantic_Sentimental_mp3']
    },
    'mysterious': {
        'keywords': ['신비', '미스터리', '불가사의', '수수께끼', '호기심'],
        'folders': ['Underscoring_mp3', 'Electronic_mp3']
    },
    'suspense': {
        'keywords': ['긴장', '스릴', '서스펜스', '조마조마'],
        'folders': ['Underscoring_mp3', 'Epic_Dramatic_mp3']
    },
    'horror': {
        'keywords': ['공포', '무서운', '두려움', '섬뜩한', '오싹한'],
        'folders': ['Horror_mp3']
    },
    'action': {
        'keywords': ['액션', '전투', '격렬', '싸움', '강렬한'],
        'folders': ['Epic_Dramatic_mp3', 'Electronic_mp3']
    },
    'fantasy': {
        'keywords': ['판타지', '마법', '환상', '신비로운'],
        'folders': ['Fantasy_mp3', 'World_mp3']
    },
    'epic': {
        'keywords': ['웅장', '장엄', '대서사', '영웅적', '위대한'],
        'folders': ['Epic_Dramatic_mp3']
    },
    'comedy': {
        'keywords': ['코미디', '재미있는', '유쾌한', '웃긴', '경쾌한'],
        'folders': ['Comedy_mp3', 'Uplifting_mp3']
    },
    'uplifting': {
        'keywords': ['신나는', '즐거운', '활기찬', '상쾌한', '밝은'],
        'folders': ['Uplifting_mp3', 'Electronic_mp3']
    },
    'sad': {
        'keywords': ['슬픈', '우울', '애수', '비극적', '눈물'],
        'folders': ['Romantic_Sentimental_mp3', 'Underscoring_mp3']
    },
    'exploration': {
        'keywords': ['탐험', '모험', '여행', '발견', '탐사'],
        'folders': ['Fantasy_mp3', 'World_mp3', 'Miscellaneous_World_Folk_mp3']
    },
    'dramatic': {
        'keywords': ['드라마틱', '극적', '강렬', '감동적'],
        'folders': ['Epic_Dramatic_mp3', 'Romantic_Sentimental_mp3']
    },
    'tension': {
        'keywords': ['긴장감', '팽팽한', '압박', '조급한'],
        'folders': ['Underscoring_mp3', 'Electronic_mp3']
    },
    'wonder': {
        'keywords': ['경이', '놀라운', '신기한', '감탄'],
        'folders': ['Fantasy_mp3', 'Uplifting_mp3']
    },
    'curious': {
        'keywords': ['호기심', '궁금한', '흥미로운'],
        'folders': ['Underscoring_mp3', 'World_mp3']
    },
    'isolation': {
        'keywords': ['고립', '외로운', '쓸쓸한', '단절'],
        'folders': ['Underscoring_mp3', 'Miscellaneous_Chill_mp3']
    },
    'nostalgic': {
        'keywords': ['향수', '그리운', '추억', '옛날'],
        'folders': ['Miscellaneous_Classical_mp3', 'Miscellaneous_Jazz_mp3']
    },
    'dark_comedy': {
        'keywords': ['블랙코미디', '아이러니', '냉소적'],
        'folders': ['Comedy_mp3', 'Underscoring_mp3']
    }
}

# Mood similarity mapping (for fallback when no files found)
MOOD_SIMILARITY = {
    'peaceful': ['nostalgic', 'isolation', 'romantic'],
    'romantic': ['peaceful', 'sad', 'nostalgic'],
    'mysterious': ['curious', 'suspense', 'wonder'],
    'suspense': ['tension', 'mysterious', 'horror'],
    'horror': ['suspense', 'tension', 'dark_comedy'],
    'action': ['epic', 'tension', 'uplifting'],
    'fantasy': ['wonder', 'exploration', 'mysterious'],
    'epic': ['action', 'dramatic', 'fantasy'],
    'comedy': ['uplifting', 'dark_comedy', 'peaceful'],
    'uplifting': ['comedy', 'action', 'wonder'],
    'sad': ['romantic', 'nostalgic', 'isolation'],
    'exploration': ['fantasy', 'wonder', 'curious'],
    'dramatic': ['epic', 'sad', 'romantic'],
    'tension': ['suspense', 'action', 'horror'],
    'wonder': ['fantasy', 'exploration', 'uplifting'],
    'curious': ['mysterious', 'exploration', 'wonder'],
    'isolation': ['sad', 'peaceful', 'nostalgic'],
    'nostalgic': ['sad', 'romantic', 'peaceful'],
    'dark_comedy': ['comedy', 'horror', 'suspense']
}

# Cache configuration
GPT_CACHE_MAX_SIZE = 100
GPT_CACHE_EXPIRY_HOURS = 24
URL_CACHE_EXPIRY_MINUTES = 50  # Regenerate before 60-min expiration
RECENT_TRACKS_SIZE = 10  # Number of recent tracks to avoid

# Global caches
gpt_cache: Dict[str, Dict] = {}  # {prompt_hash: {result: dict, timestamp: float}}
url_cache: Dict[str, Dict] = {}  # {blob_name: {url: str, timestamp: float}}
recent_tracks: Deque[str] = deque(maxlen=RECENT_TRACKS_SIZE)


def get_prompt_hash(prompt: str) -> str:
    """Generate hash for prompt caching"""
    return hashlib.md5(prompt.encode('utf-8')).hexdigest()


def get_cached_gpt_response(prompt: str) -> Optional[Dict]:
    """Retrieve cached GPT response if available and not expired"""
    prompt_hash = get_prompt_hash(prompt)

    if prompt_hash not in gpt_cache:
        return None

    cached = gpt_cache[prompt_hash]
    age_hours = (time.time() - cached['timestamp']) / 3600

    if age_hours > GPT_CACHE_EXPIRY_HOURS:
        # Expired, remove from cache
        del gpt_cache[prompt_hash]
        logger.info(f"GPT cache expired for prompt hash: {prompt_hash}")
        return None

    logger.info(f"GPT cache hit for prompt hash: {prompt_hash} (age: {age_hours:.2f}h)")
    return cached['result']


def cache_gpt_response(prompt: str, result: Dict):
    """Cache GPT response with timestamp"""
    prompt_hash = get_prompt_hash(prompt)

    # LRU eviction if cache is full
    if len(gpt_cache) >= GPT_CACHE_MAX_SIZE:
        # Remove oldest entry
        oldest_key = min(gpt_cache.keys(), key=lambda k: gpt_cache[k]['timestamp'])
        del gpt_cache[oldest_key]
        logger.info(f"GPT cache full, evicted oldest entry")

    gpt_cache[prompt_hash] = {
        'result': result,
        'timestamp': time.time()
    }
    logger.info(f"Cached GPT response for prompt hash: {prompt_hash}")


def get_cached_signed_url(blob_name: str) -> Optional[str]:
    """Retrieve cached signed URL if available and not expired"""
    if blob_name not in url_cache:
        return None

    cached = url_cache[blob_name]
    age_minutes = (time.time() - cached['timestamp']) / 60

    if age_minutes > URL_CACHE_EXPIRY_MINUTES:
        # Expired, remove from cache
        del url_cache[blob_name]
        logger.info(f"URL cache expired for: {blob_name}")
        return None

    logger.info(f"URL cache hit for: {blob_name} (age: {age_minutes:.2f}m)")
    return cached['url']


def cache_signed_url(blob_name: str, url: str):
    """Cache signed URL with timestamp"""
    url_cache[blob_name] = {
        'url': url,
        'timestamp': time.time()
    }
    logger.info(f"Cached signed URL for: {blob_name}")


def analyze_scene_with_gpt(prompt: str, retry_count: int = 3) -> Dict:
    """
    Analyze scene description using GPT-3.5 with caching and retry
    """
    # Check cache first
    cached_result = get_cached_gpt_response(prompt)
    if cached_result:
        return cached_result

    system_prompt = """당신은 게임 스토리 분석 전문가입니다.
주어진 에피소드나 씬 설명을 분석하여 적합한 배경음악의 무드를 추천해주세요.

사용 가능한 무드:
- peaceful (평화로운, 차분한)
- romantic (로맨틱한, 사랑스러운)
- mysterious (신비로운, 미스터리한) - 호기심, 궁금증이 있을 때
- suspense (긴장감 있는, 스릴 있는) - 긴장되지만 공포스럽지 않은
- horror (공포스러운, 무서운) - 두려움, 공포가 있을 때만
- action (액션, 전투)
- fantasy (판타지, 마법)
- epic (웅장한, 서사적인)
- comedy (코미디, 유쾌한)
- uplifting (신나는, 활기찬)
- sad (슬픈, 우울한)
- exploration (탐험, 모험)
- dramatic (극적인, 드라마틱한)
- tension (긴장감, 팽팽한)
- wonder (경이로운, 놀라운)
- curious (호기심 많은, 흥미로운)
- isolation (고립된, 외로운)
- nostalgic (향수, 그리운)
- dark_comedy (블랙코미디, 냉소적)

중요:
1. "호기심"이나 "궁금증"은 'mysterious' 또는 'curious'를 선택하세요 (horror 아님)
2. "긴장"은 'suspense' 또는 'tension'을 선택하세요 (horror 아님)
3. "두려움"이나 "공포"가 명시적으로 있을 때만 'horror'를 선택하세요

JSON 형식으로 응답해주세요:
{
  "primary_mood": "무드명",
  "secondary_mood": "무드명 또는 null",
  "intensity": 0.0-1.0,
  "emotional_tags": ["감정태그들"],
  "reasoning": "선택 이유 설명"
}"""

    # Retry logic
    last_error = None
    for attempt in range(retry_count):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            analysis = json.loads(response.choices[0].message.content)
            logger.info(f"GPT Analysis (attempt {attempt + 1}): {analysis}")

            # Cache the result
            cache_gpt_response(prompt, analysis)

            return analysis

        except Exception as e:
            last_error = e
            logger.warning(f"GPT analysis attempt {attempt + 1} failed: {e}")
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

    # All retries failed, return default
    logger.error(f"GPT analysis failed after {retry_count} attempts: {last_error}")
    return {
        "primary_mood": "peaceful",
        "secondary_mood": None,
        "intensity": 0.5,
        "emotional_tags": [],
        "reasoning": "GPT 분석 실패로 기본 무드 사용"
    }


def post_process_mood(analysis: Dict, original_prompt: str) -> Dict:
    """
    Post-process mood selection to fix common GPT misclassifications
    """
    prompt_lower = original_prompt.lower()

    # Keywords that should override GPT's mood selection
    mood_keywords = {
        'mysterious': ['호기심', '궁금', '신비'],
        'curious': ['호기심', '궁금한'],
        'suspense': ['긴장', '긴장감'],
        'horror': ['두려움', '공포', '무서운', '섬뜩']
    }

    for mood, keywords in mood_keywords.items():
        for keyword in keywords:
            if keyword in prompt_lower:
                if mood == 'horror' and analysis['primary_mood'] != 'horror':
                    # Only override to horror if explicitly horror-related
                    if any(k in prompt_lower for k in ['두려움', '공포', '무서운', '섬뜩']):
                        logger.info(f"Post-processing: Overriding mood to {mood} (found keyword: {keyword})")
                        analysis['primary_mood'] = mood
                        return analysis
                elif mood in ['mysterious', 'curious'] and analysis['primary_mood'] == 'horror':
                    # Prevent horror when it should be mysterious/curious
                    logger.info(f"Post-processing: Overriding mood to {mood} (found keyword: {keyword})")
                    analysis['primary_mood'] = mood
                    return analysis

    return analysis


def select_music_from_mood(mood: str, avoid_duplicates: bool = True) -> str:
    """
    Select a random music file from folders associated with the given mood
    Avoids recently played tracks
    """
    if mood not in MUSIC_LIBRARY:
        logger.warning(f"Mood '{mood}' not found in library, using 'peaceful'")
        mood = 'peaceful'

    mood_info = MUSIC_LIBRARY[mood]
    folders = mood_info['folders']

    # Get all files from the specified folders
    all_files = gcs_manager.get_files_from_folders(folders)

    if not all_files:
        # Try similar moods as fallback
        logger.warning(f"No files found for mood '{mood}', trying similar moods")
        similar_moods = MOOD_SIMILARITY.get(mood, [])

        for similar_mood in similar_moods:
            similar_folders = MUSIC_LIBRARY[similar_mood]['folders']
            all_files = gcs_manager.get_files_from_folders(similar_folders)
            if all_files:
                logger.info(f"Using similar mood '{similar_mood}' instead of '{mood}'")
                mood = similar_mood
                break

        if not all_files:
            logger.error(f"No files found for mood '{mood}' or similar moods")
            raise HTTPException(status_code=404, detail=f"No music files found for mood '{mood}'")

    # Filter out recently played tracks
    if avoid_duplicates and len(all_files) > RECENT_TRACKS_SIZE:
        available_files = [f for f in all_files if f not in recent_tracks]
        if available_files:
            all_files = available_files
            logger.info(f"Filtered out {len(recent_tracks)} recent tracks, {len(all_files)} available")

    # Select random file
    selected_file = random.choice(all_files)

    # Add to recent tracks
    recent_tracks.append(selected_file)

    logger.info(f"Selected file: {selected_file} for mood '{mood}'")
    return selected_file


@app.post("/api/analyze", response_model=AnalyzeResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def analyze(request: AnalyzeRequest):
    """
    Main endpoint: Analyze scene and return music recommendation with GCS streaming URL
    """
    try:
        prompt = request.prompt
        logger.info(f"Received prompt: {prompt}")

        # Step 1: Analyze with GPT (with caching and retry)
        analysis_dict = analyze_scene_with_gpt(prompt)

        # Step 2: Post-process mood
        analysis_dict = post_process_mood(analysis_dict, prompt)

        # Step 3: Select music file (with duplicate prevention)
        mood = analysis_dict['primary_mood']
        selected_file = select_music_from_mood(mood)

        # Step 4: Generate signed URL (with caching)
        cached_url = get_cached_signed_url(selected_file)
        if cached_url:
            streaming_url = cached_url
        else:
            streaming_url = gcs_manager.generate_signed_url(selected_file)
            if streaming_url:
                cache_signed_url(selected_file, streaming_url)

        if not streaming_url:
            raise HTTPException(status_code=500, detail="Failed to generate streaming URL")

        # Step 5: Prepare response
        analysis = MusicAnalysis(**analysis_dict)
        music = MusicInfo(
            mood=mood,
            filename=os.path.basename(selected_file),
            file_path=selected_file,
            streaming_url=streaming_url
        )

        response = AnalyzeResponse(analysis=analysis, music=music)
        logger.info(f"Response prepared successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/moods", response_model=Dict[str, MoodInfo])
async def get_moods():
    """
    List all available moods and their mapped folders
    """
    moods_info = {}
    for mood, info in MUSIC_LIBRARY.items():
        moods_info[mood] = MoodInfo(
            keywords=info['keywords'],
            folders=info['folders']
        )
    return moods_info


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint with cache statistics
    """
    return HealthResponse(
        status="healthy",
        version="3.1-Enhanced",
        gcs_bucket=os.getenv('GCS_BUCKET_NAME', ''),
        total_files=len(gcs_manager.all_files)
    )


@app.get("/api/cache/stats")
async def cache_stats():
    """
    Cache statistics endpoint
    """
    return {
        "gpt_cache": {
            "size": len(gpt_cache),
            "max_size": GPT_CACHE_MAX_SIZE,
            "expiry_hours": GPT_CACHE_EXPIRY_HOURS
        },
        "url_cache": {
            "size": len(url_cache),
            "expiry_minutes": URL_CACHE_EXPIRY_MINUTES
        },
        "recent_tracks": {
            "size": len(recent_tracks),
            "max_size": RECENT_TRACKS_SIZE,
            "tracks": list(recent_tracks)
        }
    }


@app.post("/api/cache/clear")
async def clear_cache():
    """
    Clear all caches
    """
    global gpt_cache, url_cache, recent_tracks

    gpt_cache_size = len(gpt_cache)
    url_cache_size = len(url_cache)
    tracks_size = len(recent_tracks)

    gpt_cache = {}
    url_cache = {}
    recent_tracks = deque(maxlen=RECENT_TRACKS_SIZE)

    logger.info("All caches cleared")

    return {
        "message": "All caches cleared",
        "cleared": {
            "gpt_cache": gpt_cache_size,
            "url_cache": url_cache_size,
            "recent_tracks": tracks_size
        }
    }


@app.get("/")
async def index():
    """
    Serve test client HTML
    """
    return FileResponse('music_test_client.html')


@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    # Verify GCS connection
    if gcs_manager.verify_connection():
        logger.info("GCS connection verified successfully")
        logger.info(f"Total files loaded: {len(gcs_manager.all_files)}")
    else:
        logger.error("GCS connection failed! Check your credentials and bucket name.")

    logger.info("FastAPI Music Streaming Service started successfully")
    logger.info(f"Version: 3.1-Enhanced with caching and improvements")
    logger.info(f"Documentation available at http://localhost:{os.getenv('PORT', 8003)}/docs")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8003))

    logger.info(f"Starting FastAPI Music Streaming Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
