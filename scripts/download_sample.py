
import subprocess
import sys
from pathlib import Path

# Updated with a protest-related video query
# "protest news broadcast"
# Using a specific video ID if possible, or search
# Let's try to search for a generic news clip about a protest which usually has crowd noise

def download_audio(query="ytsearch1:protest news broadcast crowd noise", output="messy.wav"):
    print(f"Downloading from: {query}")
    
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "wav",
        "-o", output,
        "--force-overwrites",
        # Use a specific known video if search fails or is flaky
        # "https://www.youtube.com/watch?v=..." 
        # But search is better for "random"
        query
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Downloaded to {output}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        return False

if __name__ == "__main__":
    # Try a specific video known to have noise/speech
    # "Protest in London" or similar
    # Let's try searching first
    download_audio("ytsearch1:protest news broadcast crowd noise")
