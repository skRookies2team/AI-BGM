"""
GCS Music Streaming Service
AI-powered music recommendation with Google Cloud Storage streaming
"""

import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
from gcs_utils import GCSMusicManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})

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


def analyze_scene_with_gpt(prompt):
    """
    Analyze scene description using GPT-3.5 and extract mood information
    """
    try:
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
        logger.info(f"GPT Analysis: {analysis}")
        return analysis

    except Exception as e:
        logger.error(f"GPT analysis failed: {e}")
        return {
            "primary_mood": "peaceful",
            "secondary_mood": None,
            "intensity": 0.5,
            "emotional_tags": [],
            "reasoning": "GPT 분석 실패로 기본 무드 사용"
        }


def post_process_mood(analysis, original_prompt):
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


def select_music_from_mood(mood):
    """
    Select a random music file from folders associated with the given mood
    """
    if mood not in MUSIC_LIBRARY:
        logger.warning(f"Mood '{mood}' not found in library, using 'peaceful'")
        mood = 'peaceful'

    mood_info = MUSIC_LIBRARY[mood]
    folders = mood_info['folders']

    # Get all files from the specified folders
    all_files = gcs_manager.get_files_from_folders(folders)

    if not all_files:
        logger.error(f"No files found for mood '{mood}' in folders {folders}")
        return None

    # Select random file
    import random
    selected_file = random.choice(all_files)

    logger.info(f"Selected file: {selected_file} for mood '{mood}'")
    return selected_file


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint: Analyze scene and return music recommendation with GCS streaming URL
    """
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        logger.info(f"Received prompt: {prompt}")

        # Step 1: Analyze with GPT
        analysis = analyze_scene_with_gpt(prompt)

        # Step 2: Post-process mood
        analysis = post_process_mood(analysis, prompt)

        # Step 3: Select music file
        mood = analysis['primary_mood']
        selected_file = select_music_from_mood(mood)

        if not selected_file:
            return jsonify({'error': 'No music file found for the selected mood'}), 404

        # Step 4: Generate signed URL
        streaming_url = gcs_manager.generate_signed_url(selected_file)

        # Step 5: Prepare response
        response = {
            'analysis': analysis,
            'music': {
                'mood': mood,
                'filename': os.path.basename(selected_file),
                'file_path': selected_file,
                'streaming_url': streaming_url
            }
        }

        logger.info(f"Response: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/moods', methods=['GET'])
def get_moods():
    """
    List all available moods and their mapped folders
    """
    moods_info = {}
    for mood, info in MUSIC_LIBRARY.items():
        moods_info[mood] = {
            'keywords': info['keywords'],
            'folders': info['folders']
        }
    return jsonify(moods_info)


@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'version': '2.0-GCS',
        'gcs_bucket': os.getenv('GCS_BUCKET_NAME'),
        'total_files': len(gcs_manager.all_files)
    })


@app.route('/')
def index():
    """
    Serve test client HTML
    """
    return send_from_directory('.', 'music_test_client.html')


if __name__ == '__main__':
    # Verify GCS connection on startup
    if gcs_manager.verify_connection():
        logger.info("GCS connection verified successfully")
        logger.info(f"Total files loaded: {len(gcs_manager.all_files)}")
    else:
        logger.error("GCS connection failed! Check your credentials and bucket name.")

    # Start Flask server
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))

    logger.info(f"Starting GCS Music Streaming Service on {host}:{port}")
    app.run(host=host, port=port, debug=os.getenv('FLASK_DEBUG', 'True') == 'True')
