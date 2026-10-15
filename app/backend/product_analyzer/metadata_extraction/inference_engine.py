import os
import faiss
import torch
import json
import requests
from io import BytesIO
from PIL import Image

from app.core.logger import system_logger
from app.backend.product_analyzer.metadata_extraction.clip_engine import CLIPEngine
from app.backend.product_analyzer.metadata_extraction.utils import clip_similarity_to_probs

class InferenceEngine:
    def __init__(self, clip_engine: CLIPEngine, content_idx_path: str, style_idx_path: str, content_labels_path: str, style_labels_path: str):
        """
        Clase encargada de implementar toda la lógica relacionada con la inferencia para una nueva imagen.
        """
        self.engine = clip_engine
        
        system_logger.info("Inference Engine: Cargando índices FAISS y etiquetas...")
        
        try:
            self.content_index = faiss.read_index(content_idx_path)
            self.style_index = faiss.read_index(style_idx_path)
            
            with open(content_labels_path, 'r') as f:
                self.content_labels = json.load(f)
            with open(style_labels_path, 'r') as f:
                self.style_labels = json.load(f)
                
            system_logger.success("Inference Engine: Índices y etiquetas listos.")
        except Exception as e:
            system_logger.error(f"Inference Engine: Error crítico al cargar los índices FAISS: {e}")
            raise e

    def predict(self, image_source: str, top_k: int = 5, threshold: float = 0.80):
        """
        Metodo encargado de realizar inferencia sobre nuestra lógica basada en índices (Soporta URLs).
        """
        system_logger.info("Inference Engine: Extrayendo metadata visual de la imagen...")
        
        try:
            if image_source.startswith("http"):
                response = requests.get(image_source)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert("RGB")
            else:
                image = Image.open(image_source).convert("RGB")
            
            with torch.no_grad():
                image_vector = self.engine.get_image_embedding(image).cpu().numpy().astype('float32')
            
            dist_c, ids_c = self.content_index.search(image_vector, top_k)
            dist_c = clip_similarity_to_probs(dist_c[0].astype(float)); ids_c = ids_c[0]
            content_results = [
                {"label": self.content_labels[idx], "score": dist_c[i]}
                for i, idx in enumerate(ids_c) if idx < len(self.content_labels) and dist_c[i] >= threshold
            ]

            dist_s, ids_s = self.style_index.search(image_vector, top_k)
            dist_s = clip_similarity_to_probs(dist_s[0].astype(float)); ids_s = ids_s[0]
            style_results = [
                {"label": self.style_labels[idx], "score": dist_s[i]}
                for i, idx in enumerate(ids_s) if idx < len(self.style_labels) and dist_s[i] >= threshold
            ]

            system_logger.success(f"Inference Engine: {len(content_results)} conceptos y {len(style_results)} estilos extraídos.")
            return content_results, style_results
            
        except Exception as e:
            system_logger.error(f"Inference Engine: Error durante la predicción - {e}")
            return [], []
    
    @staticmethod
    def generate_structured_output(image_source: str, content_results: list, style_results: list) -> str:
        """
        Estructura los resultados filtrados de la inferencia en formato JSON, limpiando URLs de Amazon.
        """
        if image_source.startswith("http"):
            image_name = image_source.split("/")[-1].split("?")
            if not image_name:
                image_name = "url_image"
        else:
            image_name = os.path.basename(image_source)
        
        structured_data = {
            "image_id": image_name,
            "metadata": {
                "content_tags": [],
                "style_tags": []
            }
        }
        
        for item in content_results:
            structured_data["metadata"]["content_tags"].append({
                "tag": item["label"],
                "probability": round(float(item["score"]), 4)
            })
            
        for item in style_results:
            structured_data["metadata"]["style_tags"].append({
                "tag": item["label"],
                "probability": round(float(item["score"]), 4)
            })
            
        return json.dumps(structured_data, indent=4, ensure_ascii=False)
