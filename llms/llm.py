import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = ''

llm = ChatOpenAI(

    model_name="gpt-4o-mini",

    temperature=0.01
)

embedding_model = OpenAIEmbeddings(

)
