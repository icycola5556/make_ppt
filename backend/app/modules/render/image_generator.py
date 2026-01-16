import os
import hashlib
import requests
from pathlib import Path
from http import HTTPStatus
from dashscope import ImageSynthesis

# Enable logging
import logging

logger = logging.getLogger(__name__)

def generate_image(prompt: str, output_dir: str, api_key: str = None) -> str | None:
    """
    Generate an image from a text prompt using DashScope (Wanx), with caching.
    
    Args:
        prompt: The text prompt for image generation.
        output_dir: Directory to save the generated image.
        api_key: Optional API key. If not provided, reads from env.
        
    Returns:
        str | None: The absolute path to the generated image if successful, None otherwise.
    """
    if not api_key:
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
    if not api_key:
        logger.error("DASHSCOPE_API_KEY not found.")
        return None

    # Implement Caching using MD5 hash of the prompt
    # distinct prompt -> distinct file
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    filename = f"{prompt_hash}.png"
    output_path = Path(output_dir) / filename
    
    # Check cache
    if output_path.exists():
        logger.info(f"[CACHE HIT] Image for prompt '{prompt[:20]}...' exists at {filename}")
        return str(output_path)

    logger.info(f"[CACHE MISS] Generating new image for prompt '{prompt[:20]}...'")

    try:
        # Call DashScope Wanx-v1 model
        rsp = ImageSynthesis.call(
            api_key=api_key,
            model=ImageSynthesis.Models.wanx_v1,
            prompt=prompt,
            n=1,
            size='1024*1024'
        )
        
        if rsp.status_code == HTTPStatus.OK:
            # Get image URL
            if rsp.output and rsp.output.results:
                img_url = rsp.output.results[0].url
                
                # Download image
                img_response = requests.get(img_url)
                if img_response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    return str(output_path)
                else:
                    logger.error(f"Failed to download image from {img_url}")
            else:
                logger.error("No results in DashScope response")
        else:
            logger.error(f"DashScope API failed: {rsp.code} - {rsp.message}")
            
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        
    return None
