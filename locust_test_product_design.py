from locust import HttpUser, task, between
import random


class ProductDesignUser(HttpUser):

    wait_time = between(2, 5)

    # -------------------------
    # 1. OPTIMIZACIÓN DE PROMPT (LLM LIGHT/MEDIUM)
    # -------------------------
    @task(2)
    def optimize_prompt(self):

        self.client.post(
            "/api/design/optimize-prompt",
            json={
                "user_idea": "modern minimal chair",
                "description": "a wooden chair with futuristic style"
            }
        )

    # -------------------------
    # 2. SEGMENTACIÓN V1 (CV HEAVY)
    # -------------------------
    @task(3)
    def segment_v1(self):

        self.client.post(
            "/api/design/segment-image-v1",
            json={
                "image": "/app/data/output/product.jpg"
            }
        )

    # -------------------------
    # 3. SEGMENTACIÓN V2 (CV + CONTEXTO)
    # -------------------------
    @task(3)
    def segment_v2(self):

        self.client.post(
            "/api/design/segment-image-v2",
            json={
                "image": "/app/data/output/product.jpg",
                "description": "a glass hourglass placed in sand",
                "visual_metadata": ["hourglass", "sand", "glass", "time"]
            }
        )
