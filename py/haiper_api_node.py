import requests
import json
import os
import time
import math
from uuid import uuid4
from PIL import Image
import torch
import shutil
import numpy as np
import comfy
from . import M2Mtoken
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the client_id and client_secret
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

class I2VPipelineNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        """
        return {
            "required": {
                "prompt": ("STRING", {"default": "add prompt here", "display": "text"}),
                "source_image": ("STRING", {"default": "add source image url here", "display": "text"}),
            },
            "optional": {
                "duration": ("INT", {"default": 6, "min": 1, "max": 6, "step": 1, "display": "number"}),
                "seed": ("INT", {"default": -1, "step": 1, "display": "number"}),
                "resolution": ("INT", {"default": 720, "step": 1, "display": "number"}),
                "is_public": ("BOOLEAN", {"default": False}),
                "is_enable_prompt_enhancer": ("BOOLEAN", {"default": False}),
                "guidance_scale": ("INT", {"default": 50, "step": 10, "display": "number"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_video_path",)

    FUNCTION = "run"

    CATEGORY = "HaiperAI"

    def run(self, prompt, source_image, duration=None, seed=None, resolution=None, is_public=None, is_enable_prompt_enhancer=None, guidance_scale=None):
        random_id = uuid4()
        directory = f"/tmp/{random_id}/"
        os.makedirs(directory, exist_ok=True)
        output_path = os.path.join(directory, "output-i2v.mp4")

        # Use the user-defined prompt instead of a hardcoded prompt
        run_status = get_video_by_i2v_pipeline(prompt, source_image, duration, seed, resolution, is_public, is_enable_prompt_enhancer, guidance_scale, output_path)

        if run_status:
            return (output_path,)
        else:
            raise RuntimeError("Run video generation failed")

class T2VPipelineNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        """
        return {
            "required": {
                "prompt": ("STRING", {"default": "add prompt here", "display": "text"}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"default": "bad, slow", "display": "text"}),
                "seed": ("INT", {"default": -1, "step": 1, "display": "number"}),
                "aspect_ratio": ("STRING", {"default": "16:9", "display": "text"}),
                "resolution": ("INT", {"default": 720, "step": 1, "display": "number"}),
                "duration": ("INT", {"default": 6, "min": 1, "max": 6, "step": 1, "display": "number"}),
                "is_public": ("BOOLEAN", {"default": False}),
                "use_ff_cond": ("BOOLEAN", {"default": True}),
                "is_enable_prompt_enhancer": ("BOOLEAN", {"default": True})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_video_path",)

    FUNCTION = "run"

    CATEGORY = "HaiperAI"

    def run(self, prompt, negative_prompt=None, seed=None, aspect_ratio=None, resolution=None, duration=None, is_public=None, use_ff_cond=None, is_enable_prompt_enhancer=None):
        random_id = uuid4()
        directory = f"/tmp/{random_id}/"
        os.makedirs(directory, exist_ok=True)

        output_path = os.path.join(directory, "output-t2v.mp4")

        # Use the user-defined prompt instead of a hardcoded prompt
        run_status = get_video_by_t2v_pipeline(prompt, negative_prompt, seed, aspect_ratio, resolution, duration, is_public, use_ff_cond, is_enable_prompt_enhancer, output_path)

        if run_status:
            return (output_path,)
        else:
            raise RuntimeError("Run video generation failed")

class T2IPipelineNode:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        """
        Return a dictionary which contains config for all input fields.
        """
        return {
            "required": {
                "prompt": ("STRING", {"default": "add prompt here", "display": "text"}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"default": "bad, slow", "display": "text"}),
                "seed": ("INT", {"default": -1, "step": 1, "display": "number"}),
                "aspect_ratio": ("STRING", {"default": "16:9", "display": "text"}),
                "resolution": ("INT", {"default": 720, "step": 1, "display": "number"}),
                "is_public": ("BOOLEAN", {"default": False}),
                "is_enable_prompt_enhancer": ("BOOLEAN", {"default": True})
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("output_image_dir_path", "output_image_0_path", "output_image_1_path", "output_image_2_path", "output_image_3_path")

    FUNCTION = "run"

    CATEGORY = "HaiperAI"

    def run(self, prompt, negative_prompt=None, seed=None, aspect_ratio=None, resolution=None, is_public=None, is_enable_prompt_enhancer=None):
        random_id = uuid4()
        directory = f"/tmp/{random_id}/"
        os.makedirs(directory, exist_ok=True)

        output_image_dir_path = directory
        output_image_0_path = os.path.join(directory, "output-image-0.jpg")
        output_image_1_path = os.path.join(directory, "output-image-1.jpg")
        output_image_2_path = os.path.join(directory, "output-image-2.jpg")
        output_image_3_path = os.path.join(directory, "output-image-3.jpg")


        # Use the user-defined prompt instead of a hardcoded prompt
        run_status = get_video_by_t2i_pipeline(prompt, negative_prompt, seed, aspect_ratio, resolution, is_public, is_enable_prompt_enhancer, output_image_0_path, output_image_1_path, output_image_2_path, output_image_3_path)

        if run_status:
            return (output_image_dir_path, output_image_0_path, output_image_1_path, output_image_2_path, output_image_3_path)
        else:
            raise RuntimeError("Run image generation failed")

def get_video_by_i2v_pipeline(prompt, source_image, duration, seed, resolution, is_public, is_enable_prompt_enhancer, guidance_scale, output_path):
    pbar = comfy.utils.ProgressBar(100)
    pbar.update_absolute(0, 100)

    try:
        # Replace with your actual API endpoint
        api_url = 'https://api1.haiper.ai/v1/jobs/gen2/image2video'
          
        payload = json.dumps({
            "prompt": prompt,  # Use the prompt provided by the user
            "config": {
              "source_image": source_image,
            },
            "settings": {
                "duration": duration,
                "seed": seed,
                "resolution": resolution,
                "guidance_scale": guidance_scale
            },
            "is_public": is_public,
            "is_enable_prompt_enhancer": is_enable_prompt_enhancer
        })

        # Get the access token
        access_token = M2Mtoken.get_token(client_id, client_secret)
        headers = {
            'x-vision-env': 'pro',
            'x-haiper-client': 'public',
            'x-haiper-auth': 'auth0',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json'
        }
      
        gen_response = requests.request("POST", api_url, headers=headers, data=payload).json()
        generation_id = gen_response['value']["generation_id"]

        # Poll the status until the video is ready
        while True:
            time.sleep(20)  # Wait for 20 seconds before checking the status
            status_url = f'https://api1.haiper.ai/v1/jobs/{generation_id}/status'
            status_response = requests.request("GET", status_url, headers=headers)
            status_data = status_response.json().get('value')
            print(status_data)

            status = status_data.get('status')
            progress = status_data.get('progress', 0)

            pbar.update_absolute(math.ceil(progress * 100), 100)

            if status == 'succeed':
                # Get watermark free video url
                get_watermark_free_video_url = f'https://api1.haiper.ai/v1/creation/{generation_id}/watermark-free-url'
                url_response = requests.request("POST", get_watermark_free_video_url, headers=headers).json()
                watermark_free_url = url_response['value']['url']

                # Download watermark free video from URL
                video_response = requests.get(watermark_free_url, stream=True)
                with open(output_path, 'wb') as video_file:
                    shutil.copyfileobj(video_response.raw, video_file)

                return True
            
            elif status == 'processing' or status == 'pending' or status == 'post_processing':
                print(f"Video is still processing (Job ID: {generation_id}). Waiting...")
                continue
            else:
                print(f"Unexpected status '{status}'. Exiting.")
                return False
            
    except Exception as error:
      print(error)

def get_video_by_t2v_pipeline(prompt, negative_prompt, seed, aspect_ratio, resolution, duration, is_public, use_ff_cond, is_enable_prompt_enhancer, output_path):
    pbar = comfy.utils.ProgressBar(100)
    pbar.update_absolute(0, 100)

    try:
        # Replace with your actual API endpoint
        api_url = 'https://api1.haiper.ai/v1/jobs/gen2/text2video'

        payload = json.dumps({
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "settings": {
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration": duration
            },
            "is_public": is_public,
            "use_ff_cond": use_ff_cond,
            "is_enable_prompt_enhancer": is_enable_prompt_enhancer
        })

        # Get the access token
        access_token = M2Mtoken.get_token(client_id, client_secret)
        headers = {
            'x-vision-env': 'pro',
            'x-haiper-client': 'public',
            'x-haiper-auth': 'auth0',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json'
        }

        gen_response = requests.request("POST", api_url, headers=headers, data=payload).json()
        generation_id = gen_response['value']["generation_id"]

        # Poll the status until the video is ready
        while True:
            time.sleep(20)  # Wait for 20 seconds before checking the status
            status_url = f'https://api1.haiper.ai/v1/jobs/{generation_id}/status'
            status_response = requests.request("GET", status_url, headers=headers)
            status_data = status_response.json().get('value')
            print(status_data)

            status = status_data.get('status')
            progress = status_data.get('progress', 0)

            pbar.update_absolute(math.ceil(progress * 100), 100)

            if status == 'succeed':
                # Get watermark free video url
                generate_watermark_free_video_url = f'https://api1.haiper.ai/v1/creation/{generation_id}/watermark-free-url'
                url_response = requests.request("POST", generate_watermark_free_video_url, headers=headers).json()
                watermark_free_url = url_response['value']['url']

                # Download watermark free video from URL
                video_response = requests.get(watermark_free_url, stream=True)
                with open(output_path, 'wb') as video_file:
                    shutil.copyfileobj(video_response.raw, video_file)

                return True

            elif status == 'processing' or status == 'pending' or status == 'post_processing':
                print(f"Video is still processing (Job ID: {generation_id}). Waiting...")
                continue
            else:
                print(f"Unexpected status '{status}'. Exiting.")
                return False

    except Exception as error:
        print(error)

def get_video_by_t2i_pipeline(prompt, negative_prompt, seed, aspect_ratio, resolution, is_public, is_enable_prompt_enhancer, output_image_0_path, output_image_1_path, output_image_2_path, output_image_3_path):
    pbar = comfy.utils.ProgressBar(100)
    pbar.update_absolute(0, 100)

    try:
        # Replace with your actual API endpoint
        api_url = 'https://api1.haiper.ai/v1/jobs/gen2/text2image'

        payload = json.dumps({
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "settings": {
                "seed": seed,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution
            },
            "is_public": is_public,
            "is_enable_prompt_enhancer": is_enable_prompt_enhancer
        })

        # Get the access token
        access_token = M2Mtoken.get_token(client_id, client_secret)
        headers = {
            'x-vision-env': 'pro',
            'x-haiper-client': 'public',
            'x-haiper-auth': 'auth0',
            'authorization': f'Bearer {access_token}',
            'content-type': 'application/json'
        }

        gen_response = requests.request("POST", api_url, headers=headers, data=payload).json()
        generation_id = gen_response['value']["generation_id"]

        # Poll the status until the video is ready
        while True:
            time.sleep(20)  # Wait for 20 seconds before checking the status
            status_url = f'https://api1.haiper.ai/v1/jobs/{generation_id}/status'
            status_response = requests.request("GET", status_url, headers=headers)
            status_data = status_response.json().get('value')
            print(status_data)

            status = status_data.get('status')
            progress = status_data.get('progress', 0)

            pbar.update_absolute(math.ceil(progress * 100), 100)

            if status == 'succeed':
                get_creation_detail_url = f'https://api1.haiper.ai/v1/creation/{generation_id}'
                # Get the image URLs
                gen_response = requests.request("GET", get_creation_detail_url, headers=headers, data=payload).json()
                output_image_0_url = gen_response['value']["outputs"][0]['media_url']
                output_image_1_url = gen_response['value']["outputs"][1]['media_url']
                output_image_2_url = gen_response['value']["outputs"][2]['media_url']
                output_image_3_url = gen_response['value']["outputs"][3]['media_url']

                # Download image from URL
                image_response = requests.get(output_image_0_url, stream=True)
                with open(output_image_0_path, 'wb') as image_file:
                    shutil.copyfileobj(image_response.raw, image_file)
                image_response = requests.get(output_image_1_url, stream=True)
                with open(output_image_1_path, 'wb') as image_file:
                    shutil.copyfileobj(image_response.raw, image_file)
                image_response = requests.get(output_image_2_url, stream=True)
                with open(output_image_2_path, 'wb') as image_file:
                    shutil.copyfileobj(image_response.raw, image_file)
                image_response = requests.get(output_image_3_url, stream=True)
                with open(output_image_3_path, 'wb') as image_file:
                    shutil.copyfileobj(image_response.raw, image_file)
                return True

            elif status == 'processing' or status == 'pending' or status == 'post_processing':
                print(f"Images are still processing (Job ID: {generation_id}). Waiting...")
                continue
            else:
                print(f"Unexpected status '{status}'. Exiting.")
                return False

    except Exception as error:
        print(error)