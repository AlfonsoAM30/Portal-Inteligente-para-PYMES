import os
import cv2
import numpy as np
import requests
import urllib.request
from segment_anything import sam_model_registry, SamPredictor
from ultralytics import YOLO, SAM

from app.backend.product_analyzer.metadata_extraction.clip_engine import CLIPEngine
from app.backend.product_analyzer.metadata_extraction.inference_engine import InferenceEngine
from app.backend.product_design.yolo_target_extractor import YoloTargetExtractor
from app.core.logger import system_logger

# --- CONFIGURACIÓN DE RUTAS EN DOCKER ---
BASE_DIR = os.getenv("CONTAINER_ROOT", os.getcwd())
MODEL_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(MODEL_DIR, exist_ok=True)

SAM_CHECKPOINT = os.path.join(MODEL_DIR, "sam_vit_b_01ec64.pth")
SAM_URL = "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth"

# 1. Descarga e inicialización de SAM Tradicional
if not os.path.exists(SAM_CHECKPOINT):
    system_logger.info("SAM: Descargando checkpoint (375MB)...")
    urllib.request.urlretrieve(SAM_URL, SAM_CHECKPOINT)

system_logger.info("SAM: Cargando modelo en memoria...")
sam = sam_model_registry["vit_b"](checkpoint=SAM_CHECKPOINT)
sam.to(device='cpu')
predictor = SamPredictor(sam)
system_logger.success("SAM: Modelo listo y a la espera.")

# 2. Carga Modelos Ultralytics (Rutas Absolutas para Docker)
system_logger.info("YOLO-World: Cargando modelo...")
yolo_model = YOLO(os.path.join(MODEL_DIR, 'yolov8m-world.pt')) 

system_logger.info("FastSAM: Cargando modelo...")
sam_model = SAM(os.path.join(MODEL_DIR, 'mobile_sam.pt')) 

yolo_extractor = YoloTargetExtractor()


def _download_or_read_image(image_source):
    """Función auxiliar para reutilizar la lógica de lectura de imágenes."""
    if isinstance(image_source, str) and image_source.startswith("http"):
        resp = requests.get(image_source, timeout=15)
        resp.raise_for_status()
        image_array = np.asarray(bytearray(resp.content), dtype="uint8")
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(image_source)

    if image is None:
        raise ValueError(f"No se pudo cargar o decodificar la imagen: {image_source}")
    return image


def get_mask_v1(image_source):
    """V1: Segmentación clásica por punto central."""
    image = _download_or_read_image(image_source)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image_rgb.shape[:2]
    
    predictor.set_image(image_rgb)

    centro_x = w // 2
    centro_y = h // 2
    input_point = np.array([[centro_x, centro_y]])
    input_label = np.array([1])

    masks, scores, _ = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True
    )
        
    best_idx = np.argmax(scores)
    final_mask = masks[best_idx]
    print(f"Índice elegido: {best_idx} | Score: {scores[best_idx]}")

    mask_uint8 = (final_mask * 255).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_uint8)

    if num_labels > 1:
        label_central = labels[centro_y, centro_x]
        if label_central > 0:
            mask_refined = (labels == label_central).astype(np.uint8) * 255
        else:
            areas = stats[1:, cv2.CC_STAT_AREA]
            if len(areas) > 0:
                largest_label = np.argmax(areas) + 1
                mask_refined = (labels == largest_label).astype(np.uint8) * 255
            else:
                mask_refined = mask_uint8
    else:
        mask_refined = mask_uint8

    kernel = np.ones((5, 5), np.uint8)
    mask_refined = cv2.morphologyEx(mask_refined, cv2.MORPH_CLOSE, kernel, iterations=3)
    mask_refined = cv2.medianBlur(mask_refined, 5)

    return mask_refined, mask_uint8


def get_mask_v2(image_source, description, visual_metadata):
    """V2: Segmentación inteligente usando CLIP + YOLO-World + FastSAM."""
    image = _download_or_read_image(image_source)
    
    search_prompts = yolo_extractor.get_search_prompts(description, visual_metadata)
    system_logger.info(f"YOLO-World: Buscando objetivos -> {search_prompts}")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    h, w = image_rgb.shape[:2]

    yolo_model.set_classes(search_prompts)
    results_yolo = yolo_model.predict(image_rgb, conf=0.1, verbose=False)[0]

    if len(results_yolo.boxes) == 0:
        system_logger.warning(f"YOLO: No se encontró '{search_prompts}'. Bounding Box central por defecto.")
        box = [w * 0.1, h * 0.1, w * 0.9, h * 0.9]
    else:
        highest_conf_idx = results_yolo.boxes.conf.argmax().item()
        box = results_yolo.boxes.xyxy[highest_conf_idx].cpu().numpy().tolist()
        system_logger.success(f"YOLO: Bounding Box enfocado -> {box}")
    
    box_prompt = [float(x) for x in box]
    
    results_sam = sam_model.predict(image_rgb, bboxes=[box_prompt], verbose=False)[0]

    if results_sam.masks is None or len(results_sam.masks.data) == 0:
        system_logger.error("FastSAM: Error generando máscara. Aplicando fallback de máscara vacía.")
        return np.ones((h, w), dtype=np.uint8) # Retorna fondo completo para evitar crashes

    mask_data = results_sam.masks.data.cpu().numpy()
    mask_data = np.squeeze(mask_data)
    
    mask_uint8 = (mask_data > 0.5).astype(np.uint8)
    mask_resized = cv2.resize(mask_uint8, (w, h), interpolation=cv2.INTER_NEAREST)

    # 5. Post-procesamiento Morfológico Avanzado
    kernel_open = np.ones((3, 3), np.uint8)
    kernel_close = np.ones((5, 5), np.uint8)
    
    mask_refined = cv2.morphologyEx(mask_resized, cv2.MORPH_OPEN, kernel_open, iterations=2)
    mask_refined = cv2.morphologyEx(mask_refined, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    mask_refined = cv2.medianBlur(mask_refined, 5)

    return 1 - mask_refined