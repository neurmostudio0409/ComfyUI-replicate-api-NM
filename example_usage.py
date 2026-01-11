"""
Simple example of using Replicate Lipsync API directly
This demonstrates the basic API usage without ComfyUI
"""

import os
import replicate
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Example: Generate a lipsynced video using Replicate API
    """
    
    print("=" * 60)
    print("🎬 Replicate Lipsync-2-Pro Example")
    print("=" * 60)
    
    # Check for API token
    api_token = os.getenv('REPLICATE_API_TOKEN')
    if not api_token:
        print("❌ Error: REPLICATE_API_TOKEN not found")
        print("\nPlease:")
        print("1. Copy .env.example to .env")
        print("2. Add your Replicate API token")
        print("3. Get token from: https://replicate.com/account/api-tokens")
        return
    
    # Set the API token
    os.environ['REPLICATE_API_TOKEN'] = api_token
    
    print("✅ API Token loaded")
    print()
    
    # Example URLs (from Replicate's documentation)
    video_url = "https://replicate.delivery/pbxt/NgWu1Skf7tZVSYYDmUVvshvZahJDPJVs4H8N7XGv4IBAoXEI/video.mp4"
    audio_url = "https://replicate.delivery/pbxt/NgWu1byVX2bBz1zp5r8uTdfXK1VH6MBkizafKZ2wF53Q0OUh/audio.mp3"
    
    print("📹 Video URL:", video_url)
    print("🎵 Audio URL:", audio_url)
    print()
    
    # Run the model
    try:
        print("🚀 Running lipsync-2-pro model...")
        print("⏳ This may take 1-3 minutes...")
        print()
        
        output = replicate.run(
            "sync/lipsync-2-pro",
            input={
                "video": video_url,
                "audio": audio_url,
                "sync_mode": "loop",        # Options: "loop" or "trim"
                "temperature": 0.5,         # 0.0 - 1.0 (expressiveness)
                "active_speaker": False     # Auto-detect active speaker
            }
        )
        
        print("✅ Generation completed!")
        print()
        
        # Get the output URL
        if hasattr(output, 'url'):
            result_url = output.url
        elif isinstance(output, str):
            result_url = output
        else:
            result_url = str(output)
        
        print("🎥 Result URL:", result_url)
        print()
        
        # Option to download
        download = input("📥 Download the video? (y/n): ").lower().strip()
        
        if download == 'y':
            output_filename = "lipsync_output.mp4"
            print(f"⬇️  Downloading to {output_filename}...")
            
            if hasattr(output, 'read'):
                # FileOutput object
                with open(output_filename, "wb") as file:
                    file.write(output.read())
            else:
                # URL string - download using requests
                import requests
                response = requests.get(result_url)
                with open(output_filename, "wb") as file:
                    file.write(response.content)
            
            print(f"✅ Downloaded to: {output_filename}")
        
        print()
        print("=" * 60)
        print("🎉 Done!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Please check:")
        print("1. Your API token is valid")
        print("2. You have sufficient credits")
        print("3. The URLs are accessible")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
