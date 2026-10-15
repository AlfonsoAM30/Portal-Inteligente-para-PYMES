from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages 

class State(TypedDict):
    # --- 1. Control de Flujo y UI ---
    logged: bool
    auth_credentials: Optional[Dict[str, str]]  
    user_data: Optional[Dict[str, Any]]   

    current_status: Optional[str]
    functional_option: Optional[str]    

    assistant_response: Optional[str]

    messages: Annotated[list, add_messages]

    # --- 2. Variables ventana Management ---
    management_prompt: Optional[str]    
    management_tool: Optional[str]      
    management_report: Optional[str]
    management_ui_payload: Optional[dict]

    # --- 3. Variables ventana Diseño (Inputs) ---
    product_image_url: Optional[str]
    product_description: Optional[str]
    product_reviews: Optional[List[str]]

    product_prompt: Optional[str]   # promp/url del producto a scrapear
    design_prompt: Optional[str]    # interacción del usurio en nodo product_llm
    user_intention: Optional[str]

    # --- 4. Datos transversales
    matadata_extracted: Optional[List[str]]
    
    # --- 5. Rama Generación Entorno (Intermedios y Output) ---
    mask_path: Optional[str]
    positive_prompt: Optional[str]
    negative_prompt: Optional[str]
    descriptive_prompt: Optional[str]
    generated_img_url: Optional[str]

    # --- 6. Rama Análisis (Intermedios y Output) ---
    keywords_extracted: Optional[List[str]]
    analysis_result: Optional[str]

    # --- 7. Control de Errores ---
    error: Optional[str]








