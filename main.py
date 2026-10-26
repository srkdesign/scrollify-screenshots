import os
import cv2
import numpy as np
from PIL import Image
from glob import glob
import subprocess

# ---- CONFIGURATION ----
input_folder = "input"
output_folder = "output"

frame_width = 1920
frame_height = 1080
fps = 60
pause_duration = 15  # frames to pause at start and end

os.makedirs(output_folder, exist_ok=True)

# ---- FFMPEG COMPRESSION FUNCTION ----
def compress_video_ffmpeg(input_path, output_path):
    print(f"[↪] Compressing with ffmpeg: {output_path}")

    command = [
        "ffmpeg",
        "-y",  # overwrite output
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "23",         # adjust 18–28 (lower is better quality)
        "-preset", "slow",    # slower = better compression
        "-movflags", "+faststart",  # for streaming
        "-pix_fmt", "yuv420p",
        output_path
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    print(f"[✔] Compressed video saved as {output_path}")

# ---- MAIN IMAGE TO VIDEO FUNCTION ----
def process_image(image_path):
    print(f"[→] Processing: {image_path}")
    img = Image.open(image_path).convert("RGB")
    img_width, img_height = img.size

    # Center crop horizontally
    if img_width > frame_width:
        offset_x = (img_width - frame_width) // 2
        img = img.crop((offset_x, 0, offset_x + frame_width, img_height))

    img_np = np.array(img)

    max_scroll_y = img_height - frame_height
    if max_scroll_y < 0:
        max_scroll_y = 0

    scroll_speed = 200  # pixels/sec
    scroll_duration = max_scroll_y / scroll_speed if max_scroll_y > 0 else 1
    total_frames = int(scroll_duration * fps)

    # Prepare paths
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    raw_video_path = os.path.join(output_folder, f"{base_name}_raw.avi")
    final_video_path = os.path.join(output_folder, f"{base_name}_scroll.mp4")

    # Initialize OpenCV VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_out = cv2.VideoWriter(raw_video_path, fourcc, fps, (frame_width, frame_height))

    # --- Pause at start ---
    start_frame = img_np[0:frame_height, :, :]
    for _ in range(pause_duration):
        video_out.write(cv2.cvtColor(start_frame, cv2.COLOR_RGB2BGR))

    # --- Scrolling frames (linear) ---
    for i in range(total_frames):
        t = i / (total_frames - 1) if total_frames > 1 else 0
        scroll_y = int(t * max_scroll_y)
        frame = img_np[scroll_y:scroll_y + frame_height, :, :]
        video_out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    # --- Pause at end ---
    for _ in range(pause_duration):
        video_out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

    video_out.release()
    print(f"[→] Raw video saved: {raw_video_path}")

    # --- Compress with ffmpeg ---
    compress_video_ffmpeg(raw_video_path, final_video_path)

    # --- Remove raw video to save SSD writes ---
    os.remove(raw_video_path)
    print(f"[🗑] Removed raw video: {raw_video_path}")

# ---- MAIN LOOP ----
def main():
    extensions = ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp")
    image_files = []
    for ext in extensions:
        image_files.extend(glob(os.path.join(input_folder, ext)))

    if not image_files:
        print("[!] No images found in input folder.")
        return

    for image_path in image_files:
        process_image(image_path)

if __name__ == "__main__":
    main()
