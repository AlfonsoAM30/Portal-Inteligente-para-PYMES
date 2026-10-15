import os
import clip
import torch
from PIL import Image

from app.core.logger import system_logger 

class CLIPEngine:
    def __init__(self, model_name="ViT-B/32", device="cpu"):
        self.device = device
        self.model_dir = "/app/models"
        os.makedirs(self.model_dir, exist_ok=True)

        try:
            system_logger.info(f"Metadata Extractor [CLIP]: Buscando/Descargando modelo '{model_name}' en: {self.model_dir}...")
            
            self.model, self.preprocess = clip.load(
                model_name, 
                device=self.device, 
                download_root=self.model_dir
            )
            system_logger.success("Metadata Extractor [CLIP]: Modelo listo en memoria.")
            
        except Exception as e:
            system_logger.error(f"Metadata Extractor [CLIP]: Error al cargar CLIP: {e}. Revisa conexión o permisos en {self.model_dir}")
            raise e

    def get_image_embedding(self, pil_image: Image):
        """
        Función encargada de calcular el embedding de una imagen haciendo uso del encoder seleccionado.
        """
        system_logger.info("Metadata Extractor [CLIP]: Calculando embedding de imagen...")
        image = self.preprocess(pil_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            features = self.model.encode_image(image)
        return self.__normalize(features)

    def get_batch_image_embeddings(self, images_batch: torch.Tensor):
        """
        Función optimizada para calcular embeddings de un batch de imágenes ya en formato de tensor.
        """
        system_logger.info(f"Metadata Extractor [CLIP]: Calculando embeddings para batch de {len(images_batch)} imágenes...")
        images_batch = images_batch.to(self.device)
        with torch.no_grad():
            features = self.model.encode_image(images_batch)
        return self.__normalize(features)

    def get_text_embeddings(self, texts):
        """
        Función encargada de calcular el embedding de un texto haciendo uso del encoder seleccionado.
        """
        system_logger.info("Metadata Extractor [CLIP]: Calculando embedding de texto...")
        tokens = clip.tokenize(texts).to(self.device)
        with torch.no_grad():
            features = self.model.encode_text(tokens)
        return self.__normalize(features)

    def __normalize(self, features):
        """
        Función privada encargada de la normalización de los embeddings
        """
        return (features / features.norm(dim=-1, keepdim=True))