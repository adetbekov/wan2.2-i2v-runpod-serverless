import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # For Base64 error handling
import time
import shutil # For file copying
# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())

# ComfyUI input directory path
COMFYUI_INPUT_DIR = "/ComfyUI/input"

def process_image_path(image_path, task_id):
    """
    Processes image_path input. Supports the following:
    1. HTTP/HTTPS URL - Downloads and saves to ComfyUI input directory
    2. Local file path - Copies to ComfyUI input directory

    Returns: Filename that ComfyUI can use
    """
    if not isinstance(image_path, str):
        raise ValueError("image_path must be a string")

    # Check for URL (starts with http:// or https://)
    if image_path.startswith('http://') or image_path.startswith('https://'):
        logger.info(f"Downloading image from URL: {image_path}")
        try:
            # Extract file extension from URL (default to .jpg if not found)
            ext = os.path.splitext(urllib.parse.urlparse(image_path).path)[1] or '.jpg'
            filename = f"{task_id}_input{ext}"
            file_path = os.path.join(COMFYUI_INPUT_DIR, filename)

            # Create directory if it doesn't exist
            os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)

            # Download image from URL
            urllib.request.urlretrieve(image_path, file_path)
            logger.info(f"Downloaded image to: {file_path}")
            return filename  # ComfyUI only needs the filename within input directory
        except Exception as e:
            raise ValueError(f"Failed to download image from URL: {e}")

    # Treat as local file path - copy to ComfyUI input directory
    logger.info(f"Processing local file path: {image_path}")

    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")

    # Extract file extension
    ext = os.path.splitext(image_path)[1] or '.jpg'
    filename = f"{task_id}_input{ext}"
    file_path = os.path.join(COMFYUI_INPUT_DIR, filename)

    # Create directory if it doesn't exist
    os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)

    # Copy file to ComfyUI input directory
    shutil.copy2(image_path, file_path)
    logger.info(f"Copied local file to: {file_path}")

    return filename  # ComfyUI only needs the filename within input directory

def process_image_base64(image_base64, task_id):
    """
    Processes Base64 image input.
    Decodes and saves to ComfyUI input directory.

    Returns: Filename that ComfyUI can use
    """
    if not isinstance(image_base64, str):
        raise ValueError("image_base64 must be a string")

    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if image_base64.startswith('data:'):
            image_base64 = image_base64.split(',', 1)[1]

        # Attempt base64 decoding
        decoded_data = base64.b64decode(image_base64, validate=True)

        # Save to file
        filename = f"{task_id}_input.jpg"
        file_path = os.path.join(COMFYUI_INPUT_DIR, filename)

        # Create directory if it doesn't exist
        os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(decoded_data)

        logger.info(f"Saved base64 image to: {file_path}")
        return filename  # ComfyUI only needs the filename within input directory

    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Failed to decode base64 image: {e}")
    
def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # Read file directly using fullpath and encode to base64
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # Process image input: either image_path (URL or local path) or image_base64
    image_path_input = job_input.get("image_path")
    image_base64_input = job_input.get("image_base64")

    # Ensure at least one image input is provided
    if not image_path_input and not image_base64_input:
        return {"error": "Either image_path or image_base64 is required"}

    # Ensure only one image input is provided
    if image_path_input and image_base64_input:
        return {"error": "Please provide either image_path or image_base64, not both"}

    try:
        if image_base64_input:
            # Process Base64 image
            image_filename = process_image_base64(image_base64_input, task_id)
            logger.info(f"Processed base64 image: {image_filename}")
        else:
            # Process image path (URL or local file)
            image_filename = process_image_path(image_path_input, task_id)
            logger.info(f"Processed image path: {image_filename}")
    except Exception as e:
        return {"error": f"Failed to process image: {e}"}

    # Check LoRA settings - process as array
    lora_pairs = job_input.get("lora_pairs", [])

    # Select appropriate workflow file based on LoRA count
    lora_count = len(lora_pairs)
    if lora_count == 0:
        workflow_file = "/wan22_nolora.json"
        logger.info("Using no LoRA workflow")
    elif lora_count == 1:
        workflow_file = "/wan22_1lora.json"
        logger.info("Using 1 LoRA pair workflow")
    elif lora_count == 2:
        workflow_file = "/wan22_2lora.json"
        logger.info("Using 2 LoRA pairs workflow")
    elif lora_count == 3:
        workflow_file = "/wan22_3lora.json"
        logger.info("Using 3 LoRA pairs workflow")
    else:
        logger.warning(f"LoRA count is {lora_count}. Maximum 3 are supported. Limiting to 3.")
        lora_count = 3
        workflow_file = "/wan22_3lora.json"
        lora_pairs = lora_pairs[:3]  # Use only first 3
    
    prompt = load_workflow(workflow_file)
    
    length = job_input.get("length", 81)
    steps = job_input.get("steps", 10)

    prompt["260"]["inputs"]["image"] = image_filename
    prompt["846"]["inputs"]["value"] = length
    prompt["246"]["inputs"]["value"] = job_input["prompt"]
    prompt["835"]["inputs"]["noise_seed"] = job_input["seed"]
    prompt["830"]["inputs"]["cfg"] = job_input["cfg"]
    prompt["849"]["inputs"]["value"] = job_input["width"]
    prompt["848"]["inputs"]["value"] = job_input["height"]

    # Apply step settings
    if "834" in prompt:
        prompt["834"]["inputs"]["steps"] = steps
        logger.info(f"Steps set to: {steps}")
        lowsteps = int(steps*0.6)
        prompt["829"]["inputs"]["step"] = lowsteps
        logger.info(f"LowSteps set to: {lowsteps}")

    # Apply LoRA settings
    if lora_count > 0:
        # LoRA node ID mapping (LoRA node IDs differ in each workflow)
        lora_node_mapping = {
            1: {
                "high": ["282"],
                "low": ["286"]
            },
            2: {
                "high": ["282", "339"],
                "low": ["286", "337"]
            },
            3: {
                "high": ["282", "339", "340"],
                "low": ["286", "337", "338"]
            }
        }
        
        current_mapping = lora_node_mapping[lora_count]
        
        for i, lora_pair in enumerate(lora_pairs):
            if i < lora_count:
                lora_high = lora_pair.get("high")
                lora_low = lora_pair.get("low")
                lora_high_weight = lora_pair.get("high_weight", 1.0)
                lora_low_weight = lora_pair.get("low_weight", 1.0)

                # HIGH LoRA settings
                if i < len(current_mapping["high"]):
                    high_node_id = current_mapping["high"][i]
                    if high_node_id in prompt and lora_high:
                        prompt[high_node_id]["inputs"]["lora_name"] = lora_high
                        prompt[high_node_id]["inputs"]["strength_model"] = lora_high_weight
                        logger.info(f"LoRA {i+1} HIGH applied: {lora_high} with weight {lora_high_weight}")

                # LOW LoRA settings
                if i < len(current_mapping["low"]):
                    low_node_id = current_mapping["low"][i]
                    if low_node_id in prompt and lora_low:
                        prompt[low_node_id]["inputs"]["lora_name"] = lora_low
                        prompt[low_node_id]["inputs"]["strength_model"] = lora_low_weight
                        logger.info(f"LoRA {i+1} LOW applied: {lora_low} with weight {lora_low_weight}")

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")

    # First, check if HTTP connection is available
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")

    # Check HTTP connection (max 3 minutes)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP connection successful (attempt {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP connection failed (attempt {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("Cannot connect to ComfyUI server. Please check if the server is running.")
            time.sleep(1)

    ws = websocket.WebSocket()
    # Attempt WebSocket connection (max 3 minutes)
    max_attempts = int(180/5)  # 3 minutes (attempt every 5 seconds)
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"WebSocket connection successful (attempt {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"WebSocket connection failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("WebSocket connection timeout (3 minutes)")
            time.sleep(5)
    videos = get_videos(ws, prompt)
    ws.close()

    # Handle case when no videos are found
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}

    return {"error": "No videos found."}

runpod.serverless.start({"handler": handler})