import ollama
from langchain_ollama import ChatOllama

class LLMConnection:
    def __init__(self, model_name="llama3.1:8b"):
        self.model = model_name
        self.client = ollama.Client(host="http://host.docker.internal:11434")
        self.client = ollama.Client()

    def test_connection(self):
        """
        Función encargada de verifica si el servidor de Ollama está activo y el modelo disponible.
        """
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def ask_llama(self, system_message, user_message):
        """
        Función encargada de enviar una consulta al modelo local.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message},
                ],
                options={'temperature': 0.3, 'num_predict': 1000},
            )
            return response['message']['content']
        except Exception as e:
            return f"❌ Error en la comunicación con Llama 3.1: {e}"

    def ask_llama_stream(self, system_message, user_message):
        """
        Función encargada de enviar una consulta al modelo local.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_message},
                    {'role': 'user', 'content': user_message},
                ],
                options={'temperature': 0.3, 'num_predict': 1000},

                stream=True
            )
            return response
        except Exception as e:
            return f"❌ Error en la comunicación con Llama 3.1: {e}"


llm = LLMConnection()
graph_llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    base_url="http://host.docker.internal:11434"
)
graph_llm_local = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    base_url="http://localhost:11434"
)