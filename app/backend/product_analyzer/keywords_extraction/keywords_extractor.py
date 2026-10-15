import spacy
from collections import Counter
from keybert import KeyBERT

from app.core.logger import system_logger

class ReviewsAnalyzer:
    def __init__(self, spacy_model: str = "es_core_news_sm"):
        system_logger.info(f"Reviews Analyzer: Cargando modelos (Spacy: {spacy_model} & KeyBERT Multilingüe)...")
        
        try:
            self.nlp = spacy.load(spacy_model, disable=["ner", "parser"])
            self.kb_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
            self.custom_trashwords = {'disponible', 'llegar', 'llegó', 'paquete', 'producto', 'artículo', 'bueno', 'excelente', 'bien'}
            self.spanish_stopwords = list(self.nlp.Defaults.stop_words)

            system_logger.success("Reviews Analyzer: Modelos NLP listos en memoria.")
        except OSError:
            system_logger.error(f"Error: Spacy no encontró el modelo '{spacy_model}'. Ejecuta 'python -m spacy download {spacy_model}'")
            raise

    def __get_adjectives(self, text: str, top_n: int = 5) -> list[str]:
        """Extrae los adjetivos más comunes de un texto."""
        doc = self.nlp(text)
        tokens = [
            token.lemma_.lower() for token in doc 
            if token.pos_ == 'ADJ' 
            and not token.is_stop 
            and token.lemma_.lower() not in self.custom_trashwords 
            and len(token.text) > 2
        ]
        counts = Counter(tokens)
        return [word for word, _ in counts.most_common(top_n)]

    def __get_key_concepts(self, text: str, n_keywords: int = 5) -> list[str]:
        """Extrae frases clave (1 a 2 palabras) usando KeyBERT."""
        if len(text.split()) < 3:
            return []
            
        keywords = self.kb_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words=self.spanish_stopwords, 
            use_mmr=True,
            diversity=0.7,
            top_n=n_keywords
        )
        

        return [k[0] for k in keywords] 

    def extract_all_keywords(self, reviews: list[str]) -> list[str]:
        """
        Recibe una lista de reviews (que deberían ser las positivas) y devuelve
        una única lista uniendo los mejores conceptos y adjetivos.
        """
        if not reviews:
            return []

        all_text = " ".join(reviews)
        
        system_logger.info("Reviews Analyzer: Extrayendo conceptos y adjetivos...")
        
        conceptos = self.__get_key_concepts(all_text, n_keywords=5)
        adjetivos = self.__get_adjectives(all_text, top_n=5)
        
        final_keywords = list(set(conceptos + adjetivos))
        
        system_logger.success(f"Reviews Analyzer: Extraídas {len(final_keywords)} keywords únicas.")
        
        return final_keywords