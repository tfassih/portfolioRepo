import subprocess


subprocess.run([
    "ffmpeg", "-i", "input.mov", "-vf", "scale=1280:-2",
    "-c:v", "libx264", "-crf", "23", "-preset", "medium",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
    "-movflags", "+faststart", "portfolio.mp4",
], check=True)