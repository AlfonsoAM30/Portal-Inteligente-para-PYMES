import os
import requests
from io import BytesIO
import cv2
import uuid
import torch
import numpy as np
from PIL import Image
from diffusers import ControlNetModel, StableDiffusionControlNetInpaintPipeline, DDIMScheduler
from controlnet_aux import CannyDetector

from app.core.logger import system_logger

class LocalDiffusionEngine:
    def __init__(self):
        system_logger.info("Diffusion Engine: Inicializando modelos (Stable Diffusion + ControlNet)...")
        
        self.device = 'cpu'
        self.dtype = torch.float32
        self.cache_dir = '/app/models'
        self.output_dir = "/app/data/output"
        try:
            self.controlnet = ControlNetModel.from_pretrained(
                "lllyasviel/sd-controlnet-canny",
                torch_dtype=self.dtype,
                cache_dir=self.cache_dir
            )

            self.pipe = StableDiffusionControlNetInpaintPipeline.from_pretrained(
                "SG161222/Realistic_Vision_V5.1_noVAE",
                controlnet=self.controlnet,
                torch_dtype=self.dtype,
                safety_checker=None,
                cache_dir=self.cache_dir
            ).to(self.device)
            
            self.pipe.scheduler = DDIMScheduler.from_config(self.pipe.scheduler.config)

            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()

            self.canny = CannyDetector()
            system_logger.success(f"Diffusion Engine: Modelos listos en memoria usando [{self.device.upper()}]")
            
        except Exception as e:
            system_logger.error(f"Diffusion Engine: Fallo al cargar modelos - {e}")
            raise e

    def generate_image_local(self, image_url: str, mask_path: str, positive_prompt: str, negative_prompt: str = "") -> str:
        """Genera la imagen desde una URL y devuelve la ruta donde se ha guardado."""
        try:
            if not os.path.exists(mask_path) or not os.path.isfile(mask_path):
                system_logger.error(f"Diffusion Engine: ❌ No se ha encontrado la máscara en la ruta: {mask_path}")
                return None

            system_logger.info(f"Diffusion Engine: Descargando imagen original desde la URL...")
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            
            img_orig = Image.open(BytesIO(response.content)).convert("RGB")
            mask_orig = Image.open(mask_path).convert("L")
            
            w_orig, h_orig = img_orig.size

            MAX_DIM = 512  
            if w_orig > h_orig:
                new_w = MAX_DIM
                new_h = int(MAX_DIM * (h_orig / w_orig))
            else:
                new_h = MAX_DIM
                new_w = int(MAX_DIM * (w_orig / h_orig))

            new_w = (new_w // 64) * 64
            new_h = (new_h // 64) * 64

            image = img_orig.resize((new_w, new_h), Image.LANCZOS)
            mask = mask_orig.resize((new_w, new_h), Image.LANCZOS)

            image_np = np.array(image)
            mask_np = np.array(mask)
            mask_np = cv2.GaussianBlur(mask_np, (5, 5), 0)
            mask_pil = Image.fromarray(mask_np)

            control = self.canny(image_np, 100, 200, detect_resolution=new_h, image_resolution=new_h)
            if control.shape[:2] != mask_np.shape[:2]:
                control = cv2.resize(control, (new_w, new_h))
            control[mask_np > 127] = 0
            control_pil = Image.fromarray(control)

            system_logger.info("Diffusion Engine: Generando píxeles (Inpainting)...")
            result = self.pipe(
                prompt=positive_prompt,
                negative_prompt=negative_prompt,
                image=image,
                mask_image=mask_pil,
                control_image=control_pil,
                num_inference_steps=1,
                guidance_scale=7.5,
                controlnet_conditioning_scale=0.9
            ).images[0]

            final_img = result.resize((w_orig, h_orig), Image.LANCZOS)


            filename = f"gen_{uuid.uuid4().hex}.jpg" 
            os.makedirs(self.output_dir, exist_ok=True)
            final_img_save_path = os.path.join(self.output_dir, filename)
            final_img.save(final_img_save_path, format="JPEG")
            system_logger.success(f"Diffusion Engine: Imagen lista en URL: /outputs/{filename}")
            return f"/outputs/{filename}"
            

        except requests.exceptions.RequestException as e:
            system_logger.error(f"Diffusion Engine: Error descargando la imagen desde la URL - {e}")
            return None
        except Exception as e:
            system_logger.error(f"Diffusion Engine: Error durante la generación - {e}")
            return None