import os
import cv2
import numpy as np
from PIL import Image
from glob import glob

# ---- CONFIGURATION ----
input_folder = "input"
output_folder = "output"

frame_width = 1920
frame_height = 1080
fps = 60
pause_duration = 60  # frames to pause at start and end

os.makedirs(output_folder, exist_ok=True)

# ---- EASING FUNCTION ----
def ease_in_out(t):
    return 2*t*t if t < 0.5 else -1 + (4 - 2*t)*t

def process_image(image_path):
    print(f"[→] Processing: {image_path}")
    img = Image.open(image_path).convert("RGB")
    img_width, img_height = img.size

    # Center crop horizontally if needed
    if img_width > frame_width:
        offset_x = (img_width - frame_width) // 2
        img = img.crop((offset_x, 0, offset_x + frame_width, img_height))

    img_np = np.array(img)

    max_scroll_y = img_height - frame_height
    if max_scroll_y < 0:
        max_scroll_y = 0

    # Scroll speed in pixels per second
    scroll_speed = 200
    scroll_duration = max_scroll_y / scroll_speed if max_scroll_y > 0 else 1  # fallback duration 1 sec
    total_frames = int(scroll_duration * fps)

    frames = []

    # Pause at start
    start_frame = img_np[0:frame_height, :, :]
    frames.extend([start_frame.copy()] * pause_duration)

    # Scroll frames with easing
    for i in range(total_frames):
        t = i / (total_frames - 1) if total_frames > 1 else 0
        eased_t = ease_in_out(t)
        scroll_y = int(eased_t * max_scroll_y)
        frame = img_np[scroll_y:scroll_y + frame_height, :, :]
        frames.append(frame.copy())

    # Pause at end
    frames.extend([frames[-1].copy()] * pause_duration)

    # Prepare output path
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_video = os.path.join(output_folder, f"{base_name}_scroll.mp4")

    # ---- EXPORT VIDEO ----
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))
    for frame in frames:
        video_out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    video_out.release()
    print(f"[✔] Video saved as {output_video}")

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
