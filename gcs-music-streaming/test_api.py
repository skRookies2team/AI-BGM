"""
Test the Music Streaming API endpoints
"""

import requests
import json

API_BASE_URL = 'http://localhost:8003'


def print_section(title):
    """Print a section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def test_health():
    """Test health endpoint"""
    print_section("Testing Health Endpoint")

    try:
        response = requests.get(f'{API_BASE_URL}/api/health')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_moods():
    """Test moods listing endpoint"""
    print_section("Testing Moods Endpoint")

    try:
        response = requests.get(f'{API_BASE_URL}/api/moods')
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Total moods: {len(data)}")
        print(f"\nAvailable moods:")
        for mood in data.keys():
            print(f"  - {mood}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_analyze(prompt):
    """Test analyze endpoint"""
    print_section(f"Testing Analyze Endpoint: '{prompt}'")

    try:
        response = requests.post(
            f'{API_BASE_URL}/api/analyze',
            json={'prompt': prompt},
            headers={'Content-Type': 'application/json'}
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\nAnalysis Results:")
            print(f"  Primary Mood: {data['analysis']['primary_mood']}")
            print(f"  Secondary Mood: {data['analysis'].get('secondary_mood', 'None')}")
            print(f"  Intensity: {data['analysis']['intensity']}")
            print(f"  Emotional Tags: {', '.join(data['analysis']['emotional_tags'])}")
            print(f"  Reasoning: {data['analysis']['reasoning']}")

            print(f"\nMusic Selection:")
            print(f"  Filename: {data['music']['filename']}")
            print(f"  File Path: {data['music']['file_path']}")
            print(f"  Streaming URL: {data['music']['streaming_url'][:80]}...")

            # Verify it's a GCS URL
            if 'storage.googleapis.com' in data['music']['streaming_url']:
                print(f"\n  ✅ GCS signed URL detected!")
            else:
                print(f"\n  ⚠️  Warning: Not a GCS URL")

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  GCS Music Streaming API Test Suite")
    print("="*60)
    print("\nMake sure the server is running: python music_service_gcs.py")
    input("Press Enter to continue...")

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health()))

    # Test 2: Moods listing
    results.append(("Moods Listing", test_moods()))

    # Test 3: Analyze with different prompts
    test_prompts = [
        "주인공이 숲 속을 탐험하며 여관을 찾아 나선다",
        "갑작스러운 공격으로 마을이 불타오르고 전투가 시작된다",
        "주인공과 히로인이 달빛 아래에서 춤을 춘다",
        "오래된 저택에서 이상한 소리가 들리고 두려움을 느낀다"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        results.append((f"Analyze Test {i}", test_analyze(prompt)))

    # Print summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
