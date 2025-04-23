import ollama
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI


# if not os.environ.get("OPENAI_API_KEY"):
#     os.environ["OPENAI_API_KEY"] = ''
#
# llm = ChatOpenAI(
#     model_name="gpt-4o-mini",
#     temperature=0.01
# )
#
# embedding_model = OpenAIEmbeddings(
#
# )


# Initialize the Ollama embedding model

def get_llm():
    return ChatOpenAI(
        openai_api_base="",
        openai_api_key='',
        model_name='',
        temperature=0.1
    )


def embed_text(prompt: str):
    response = ollama.embeddings(model='nomic-embed-text', prompt=prompt)
    return response['embedding']


embedding_model = OllamaEmbeddings(model="nomic-embed-text:latest")
