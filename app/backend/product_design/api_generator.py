import os
import replicate
import uuid
import requests
from dotenv import load_dotenv

from app.core.logger import system_logger

load_dotenv()

def __get_input(source):
        if not source: return None
        if isinstance(source, str) and source.startswith('http'):
            return [source]
        if os.path.exists(source):
            return [open(source, 'rb')]

def generate_image_api(image, prompt):
    output = replicate.run(
            "google/nano-banana",
            input={
                "prompt": prompt,
                "image_input": __get_input(image),
                "output_format": "jpg",
                "aspect_ratio": "1:1"
            }
        )
    
    remote_url = output if isinstance(output, list) else output

    system_logger.info("API Replicate: Imagen generada. Descargando a local...")
    response = requests.get(remote_url, timeout=15)
    response.raise_for_status()

    filename = f"api_gen_{uuid.uuid4().hex}.jpg"
    output_dir = "/app/data/output"
    os.makedirs(output_dir, exist_ok=True)
    final_save_path = os.path.join(output_dir, filename)
    
    with open(final_save_path, 'wb') as f:
        f.write(response.content)
        
    system_logger.success(f"API Replicate: Imagen guardada con éxito en URL: /outputs/{filename}")
    
    return f"/outputs/{filename}"
