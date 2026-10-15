from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import cv2

from app.backend.product_design.prompt_optimization import get_optimized_prompt
from app.backend.product_design.segmentation import get_mask_v1, get_mask_v2
from app.backend.product_design.api_generator import generate_image_api
from app.backend.product_design.local_generator import LocalDiffusionEngine

app = FastAPI(title="Product Design Atomic Service")
app.mount("/outputs", StaticFiles(directory="/app/data/output"), name="outputs")

router = APIRouter(prefix="/api/design", tags=["Product Design Components"])

local_generator = LocalDiffusionEngine()

class PromptReq(BaseModel):
    user_idea: str
    description: str

class Seg_v1Req(BaseModel):
    image: str

class Seg_v2Req(BaseModel):
    image: str
    description: str
    visual_metadata: list

class LocalGenReq(BaseModel):
    image: str
    mask_path: str
    positive_prompt: str
    negative_prompt: str

class ApiGenReq(BaseModel):
    image: str
    descriptive_prompt: str


@router.post("/optimize-prompt")
def optimize_prompt(request: PromptReq):
    try:
        result = get_optimized_prompt(request.user_idea, request.description)
        return {
            "positive_prompt": result.positive_prompt,
            "negative_prompt": result.negative_prompt,
            "descriptive_prompt": result.descriptive_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/segment-image-v1")
def segment_image_v1(request: Seg_v1Req):
    try:
        mask_final = get_mask_v1(request.image)
        mask_path = "/app/logs/temporal_mask.png"
        cv2.imwrite(mask_path, mask_final * 255)
        return {"mask_path": mask_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/segment-image-v2")
def segment_image_v2(request: Seg_v2Req):
    try:
        mask_final = get_mask_v2(request.image, request.description, request.visual_metadata)
        mask_path = "/app/logs/temporal_mask.png"
        cv2.imwrite(mask_path, mask_final * 255)
        return {"mask_path": mask_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-local")
def generate_local(request: LocalGenReq):
    try:
        path = local_generator.generate_image_local(
            request.image, request.mask_path, request.positive_prompt, request.negative_prompt
        )
        return {"generated_img_url": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/generate-api")
def generate_api(request: ApiGenReq):
    try:
        output = generate_image_api(request.image, request.descriptive_prompt)
        return {"generated_img_url": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(router)
