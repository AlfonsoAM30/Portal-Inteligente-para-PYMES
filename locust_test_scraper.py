from locust import HttpUser, task, between
import random


class ProductScraperUser(HttpUser):

    wait_time = between(1, 3)

    # -------------------------
    # 1. OPTIMIZACIÓN DE PROMPT (LLM LIGHT/MEDIUM)
    # -------------------------
    @task(2)
    def get_scraper(self):

        self.client.get(
            "/api/scraper/product",
            params={
                "url": "https://www.amazon.es/Náutica-Set-fragancias-para-hombres/dp/B000P275F6/?_encoding=UTF8&pd_rd_w=atJ3w&content-id=amzn1.sym.0ed7385b-dc6d-44cf-9edb-c0e4a4416521%3Aamzn1.symc.b1464ab7-6d6a-4fc8-be8f-f2e9bcc64228&pf_rd_p=0ed7385b-dc6d-44cf-9edb-c0e4a4416521&pf_rd_r=5VE3H2CZ714HDA25MCS7&pd_rd_wg=osKYb&pd_rd_r=c028e371-1215-4bb1-a58f-140c424b5d81&ref_=pd_hp_d_btf_ci_mcx_mr_ca_id_hp_d"
            },
            name="/api/scraper/product"
        )