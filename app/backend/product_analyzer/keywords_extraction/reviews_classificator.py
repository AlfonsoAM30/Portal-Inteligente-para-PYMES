import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from app.core.logger import system_logger

class ReviewsClassifier:
    def __init__(
            self, 
            repo_id: str = "AlfonAM/Sentiment_Classifier", 
            subfolder: str = "sentiment_model_destilled",
            device: torch.device = None
        ):

        self.cache_dir = "/app/models"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.device = device if device is not None else torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        system_logger.info(f"Reviews Classifier: Cargando modelo desde {repo_id}...")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                repo_id, 
                subfolder=subfolder, 
                cache_dir=self.cache_dir
            )
            
            self.model = AutoModelForSequenceClassification.from_pretrained(
                repo_id, 
                subfolder=subfolder, 
                cache_dir=self.cache_dir
            )
            
            self.model.to(self.device)
            self.model.eval()
            
            self.id2label = {0: 'No Positive', 1: 'Positive'}
            system_logger.success("Reviews Classifier: Modelo BERT cargado en memoria.")
            
        except Exception as e:
            system_logger.error(f"Reviews Classifier: Error cargando el modelo de Hugging Face - {e}")
            raise e

    def predict(self, texts: list[str], return_labels: bool = False):
        if not texts:
            return []
            
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        )

        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        
        preds = torch.argmax(logits, dim=-1).cpu().tolist()

        if return_labels:
            return self.__map_ids(preds)
        
        return preds

    def __map_ids(self, ids: list[int]):
        return [self.id2label.get(int(x), x) for x in ids]