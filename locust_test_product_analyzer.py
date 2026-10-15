from locust import HttpUser, task, between
import random


class ProductAnalyzerUser(HttpUser):

    wait_time = between(1, 3)

    # -------------------------
    # TEST 1: METADATA (CLIP)
    # -------------------------
    @task(2)
    def extract_metadata(self):

        self.client.post(
            "/api/analyzer/extract-metadata",
            json={
                "image_source": "https://example.com/image.jpg"
            }
        )

    # -------------------------
    # TEST 2: REVIEWS ANALYSIS (LLM)
    # -------------------------
    @task(2)
    def analyze_reviews(self):

        self.client.post(
            "/api/analyzer/analyze-reviews",
            json={
                "reviews": [
                    "Great product, I love it",
                    "Muy buena calidad",
                    "fast shipping and good packaging"
                ]
            }
        )

    # -------------------------
    # TEST 3: DESCRIPTION GENERATION (LLM HEAVY)
    # -------------------------
    @task(2)
    def optimize_description(self):

        self.client.post(
            "/api/analyzer/optimize-description",
            json={
                "name_empresa": "TestBrand",
                "current_description": "Basic product description",
                "visual_tags": ["modern", "minimal", "tech"],
                "positive_keywords": ["quality", "durability", "design"],
                "tone": "professional"
            }
        )