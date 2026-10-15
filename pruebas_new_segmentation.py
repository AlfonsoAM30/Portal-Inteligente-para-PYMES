import os
import cv2
import numpy as np
import time
from ultralytics import YOLO, SAM
import matplotlib.pyplot as plt

from app.backend.product_analyzer.metadata_extraction.clip_engine import CLIPEngine
from app.backend.product_analyzer.metadata_extraction.inference_engine import InferenceEngine
from app.backend.product_design.yolo_target_extractor import YoloTargetExtractor

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# ==========================================
# CONFIGURACIÓN DE LA PRUEBA
# ==========================================
IMAGE_PATH = "data/product.jpg"  

# Archivos de salida para auditar el proceso
OUTPUT_BBOX = "data/v2_seg/1_resultado_yolo.jpg"
OUTPUT_MASK_RAW = "data/v2_seg/2_mascara_bruta.png"
OUTPUT_MASK_REFINED = "data/v2_seg/3_mascara_refinada_limpia.png"
OUTPUT_MASK_FINAL = "data/v2_seg/4_mascara_invertida_inpainting.png"
OUTPUT_CUTOUT = "data/v2_seg/5_recorte_visual_transparente.png"


clip_engine = CLIPEngine(model_name="ViT-B/32", device="cpu")
inference_engine = InferenceEngine(
    clip_engine=clip_engine,
    content_idx_path="data/content_index.bin", 
    style_idx_path="data/style_index.bin",
    content_labels_path="data/content_labels.json",
    style_labels_path="data/style_labels.json"
)

yolo_extractor = YoloTargetExtractor()

content_results, style_results = inference_engine.predict(IMAGE_PATH, top_k=10, threshold=0.85)
tags_contenido = [item["label"] for item in content_results]
tags_estilo = [item["label"] for item in style_results]
visual_metadata = tags_contenido + tags_estilo

search_prompts = yolo_extractor.get_search_prompts("No disponible", visual_metadata)

def run_pipeline():
    print("🚀 Iniciando prueba del Pipeline YOLO-World + FastSAM con Refinamiento")

    # 1. Cargar la imagen
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: No se encuentra la imagen '{IMAGE_PATH}'")
        return
        
    img_cv = cv2.imread(IMAGE_PATH)
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    h, w = img_cv.shape[:2]
    print(f"✅ Imagen cargada: {w}x{h}")

    # ==========================================
    # FASE 1: DETECCIÓN CON YOLO-WORLD (Small)
    # ==========================================
    inicio = time.time()
    print("\n⏳ Cargando YOLO-World...")
    yolo_model = YOLO('models/yolov8m-world.pt') 
    
    print(f"🔍 Buscando '{search_prompts}' en la imagen...")
    yolo_model.set_classes(search_prompts)
    results_yolo = yolo_model.predict(img_rgb, conf=0.05, verbose=False)[0]
    
    # Mecanismo de Fallback (Caja central por si falla)
    if len(results_yolo.boxes) == 0:
        print(f"⚠️ YOLO no encontró '{search_prompts}'. Usando caja central por defecto.")
        box = [w*0.2, h*0.2, w*0.8, h*0.8]
    else:
        highest_conf_idx = results_yolo.boxes.conf.argmax().item()
        box = results_yolo.boxes.xyxy[highest_conf_idx].cpu().numpy().tolist()
        print(f"✅ Bounding Box encontrado: {box}")
        
        # Guardar visualización YOLO
        img_with_box = results_yolo.plot()
        cv2.imwrite(OUTPUT_BBOX, cv2.cvtColor(img_with_box, cv2.COLOR_RGB2BGR))
        print(f"💾 Guardado: {OUTPUT_BBOX}")

    # ==========================================
    # FASE 2: SEGMENTACIÓN CON FastSAM
    # ==========================================
    print("\n⏳ Cargando FastSAM...")
    sam_model = SAM('models/mobile_sam.pt') 
    
    print("✂️ Recortando el objeto basado en el Bounding Box...")
    box_prompt = [float(x) for x in box]
    results_sam = sam_model.predict(img_rgb, bboxes=[box_prompt], verbose=False)[0]
    
    if results_sam.masks is None or len(results_sam.masks.data) == 0:
         print("❌ FastSAM no pudo generar una máscara a partir de la caja.")
         return
         
    mask_data = results_sam.masks.data.cpu().numpy()
    mask_data = np.squeeze(mask_data)
    mask_uint8 = mask_data.astype(np.uint8)
    mask_resized = cv2.resize(mask_uint8, (w, h), interpolation=cv2.INTER_NEAREST)
    plt.imsave(OUTPUT_MASK_RAW, mask_resized, cmap='gray')
    print(f"💾 Guardado: {OUTPUT_MASK_RAW}")
    

    # ==========================================
    # FASE 3: REFINAMIENTO (Tu lógica original)
    # ==========================================
    print("\n✨ Aplicando limpieza morfológica de bordes...")
    kernel_open = np.ones((3, 3), np.uint8)
    kernel_close = np.ones((5, 5), np.uint8)
    
    # Cerrar huecos internos del objeto
    mask_refined = cv2.morphologyEx(mask_resized, cv2.MORPH_OPEN, kernel_open, iterations=3)
    mask_refined = cv2.morphologyEx(mask_resized, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    
    # Suavizar bordes
    mask_refined = cv2.medianBlur(mask_refined, 5)
    
    plt.imsave(OUTPUT_MASK_REFINED, mask_refined, cmap='gray')
    print(f"💾 Guardado: {OUTPUT_MASK_REFINED}")

    # ==========================================
    # FASE 4: INVERSIÓN FINAL PARA INPAINTING
    # ==========================================
    print("🔄 Invirtiendo máscara (Fondo = 1, Objeto = 0)...")
    mask_final = 1 - mask_refined
    
    plt.imsave(OUTPUT_MASK_FINAL, mask_final, cmap='gray')
    print(f"💾 Guardado: {OUTPUT_MASK_FINAL}")

    # ==========================================
    # EXTRA: VISUALIZACIÓN DEL RECORTE
    # ==========================================
    # Usamos la máscara REFINADA (no la invertida) para que veas el objeto recortado
    alpha_channel = (mask_refined * 255).astype(np.uint8)
    b, g, r = cv2.split(img_cv)
    img_rgba = cv2.merge((b, g, r, alpha_channel))
    cv2.imwrite(OUTPUT_CUTOUT, img_rgba)
    print(f"💾 Guardado: {OUTPUT_CUTOUT}")

    print(f'{time.time() - inicio}s')

    print("\n🎉 Pipeline de prueba completado con éxito.")

if __name__ == "__main__":
    run_pipeline()