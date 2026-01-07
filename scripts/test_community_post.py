import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uploader import _get_service_sync
from community_promoter import promoter

def manual_test():
    print("🚀 Starting Manual Community Post Test...")
    print("---------------------------------------")
    
    video_url = input("Enter a valid YouTube Video URL to promote: ").strip()
    if not video_url:
        print("❌ URL required.")
        return

    n_clips = int(input("Enter number of clips (e.g. 10): ").strip() or "10")
    
    print("\n🔐 Authenticating...")
    try:
        service = _get_service_sync()
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        print("💡 Try deleting token.json and running scripts/auth_youtube.py")
        return

    print("\n📤 Attempting to post...")
    
    # Bypass async for test
    promoter._promote_sync(service, video_url, n_clips)
    
    print("\n✅ Test finished. Check your Community Tab or logs above.")
    print("Note: If nothing appeared and no error shown, the API might not support it for your channel (Silent Fail).")

if __name__ == "__main__":
    manual_test()
