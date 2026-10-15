from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
import os

# Imports oficiales de tu backend
from app.backend.product_analyzer.metadata_extraction.clip_engine import CLIPEngine
from app.backend.product_analyzer.metadata_extraction.inference_engine import InferenceEngine
from app.backend.product_analyzer.keywords_extraction.keywords_extractor import ReviewsAnalyzer
from app.backend.product_analyzer.description_generator import DescriptionGenerator
from app.core.logger import system_logger

app = FastAPI(title="Product Analyzer Service")
router = APIRouter(prefix="/api/analyzer", tags=["Product Analyzer Components"])

MODEL_DIR = "/app/models"
DATA_DIR = "/app/data"

try:
    system_logger.info("MS Analyzer: Cargando CLIP e Índices de metadatos...")
    clip_engine = CLIPEngine(model_name="ViT-B/32", device="cpu")
    inference_engine = InferenceEngine(
        clip_engine=clip_engine,
        content_idx_path=os.path.join(DATA_DIR, "content_index.bin"), 
        style_idx_path=os.path.join(DATA_DIR, "style_index.bin"),
        content_labels_path=os.path.join(DATA_DIR, "content_labels.json"),
        style_labels_path=os.path.join(DATA_DIR, "style_labels.json")
    )
    
    system_logger.info("MS Analyzer: Cargando analizadores de texto y prompts...")
    analyzer = ReviewsAnalyzer()
    description_generator = DescriptionGenerator()
    
    system_logger.success("MS Analyzer: Todos los motores de análisis listos.")
except Exception as e:
    system_logger.error(f"Fallo crítico al inicializar componentes de IA: {e}")
    inference_engine = None
    analyzer = None
    description_generator = None


class MetadataReq(BaseModel):
    image_source: str

class ReviewsReq(BaseModel):
    reviews: List[str]

class OptimizeDescReq(BaseModel):
    name_empresa: str
    current_description: str
    visual_tags: List[str]
    positive_keywords: List[str]
    tone: str


@router.post("/extract-metadata")
def extract_metadata(request: MetadataReq):
    if not inference_engine:
        raise HTTPException(status_code=503, detail="Motor CLIP/Inferencia no disponible en este contenedor.")
    try:
        content_results, style_results = inference_engine.predict(
            request.image_source, top_k=10, threshold=0.85
        )
        
        tags_contenido = [item["label"] for item in content_results]
        tags_estilo = [item["label"] for item in style_results]
        combined = tags_contenido + tags_estilo
        
        # TODO: ver como vamos a devolver
        return {
            "status": "success",
            "content_tags": tags_contenido,
            "style_tags": tags_estilo,
            "visual_metadata": combined 
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en CLIP Engine: {str(e)}")


@router.post("/analyze-reviews")
def analyze_reviews(request: ReviewsReq):
    if not analyzer:
        raise HTTPException(status_code=503, detail="Analizador de reseñas no disponible.")
    try:
        if not request.reviews:
            return {"status": "success", "positive_keywords": []}
            
        keywords = analyzer.extract_all_keywords(request.reviews)
        return {
            "status": "success",
            "positive_keywords": keywords
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando reseñas: {str(e)}")


@router.post("/optimize-description")
def optimize_description(request: OptimizeDescReq):
    if not description_generator:
        raise HTTPException(status_code=503, detail="Generador de descripciones no disponible.")
    try:
        new_description = description_generator.generate_new_product_description(
            request.name_empresa,
            request.current_description,
            request.visual_tags,
            request.positive_keywords,
            request.tone
        )
        return {
            "status": "success",
            "enhanced_description": new_description
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizando descripción: {str(e)}")

app.include_router(router)