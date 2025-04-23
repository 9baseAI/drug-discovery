from langchain_core.tools import create_retriever_tool
from langchain_qdrant import QdrantVectorStore

from llms.llm import embedding_model, get_llm
llm=get_llm()
from prompts.prompt import rag_fusion_prompt, rag_prompt, rag_fusion_prompt_3,rag_prompt_3

qdrant_retriever = QdrantVectorStore.from_existing_collection(
    embedding=embedding_model,
    collection_name='medicinal_chemistry_docs121213',
    url=f"http://localhost:6333",

).as_retriever(search_kwargs={"k": 3})

retriever_tool = create_retriever_tool(
    qdrant_retriever,
    "retrieve_my_texts",
    "Retrieve texts stored in the Qdrant collection",
)

tools = [retriever_tool]

from operator import itemgetter

from langchain.load import dumps, loads
from langchain.prompts import ChatPromptTemplate

prompt_rag_fusion = ChatPromptTemplate.from_template(rag_fusion_prompt_3)

from langchain_core.output_parsers import StrOutputParser

generate_queries = (
        prompt_rag_fusion
        | llm
        | StrOutputParser()
        | (lambda x: x.split("\n"))
)


def reciprocal_rank_fusion(results: list[list], k=3):
    """ Reciprocal_rank_fusion that takes multiple lists of ranked documents
        and an optional parameter k used in the RRF formula """

    fused_scores = {}

    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            previous_score = fused_scores[doc_str]
            fused_scores[doc_str] += 1 / (rank + k)

    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return reranked_results


retrieval_chain_rag_fusion = generate_queries | qdrant_retriever.map() | reciprocal_rank_fusion

prompt = ChatPromptTemplate.from_template(rag_prompt_3)

final_rag_chain = (
        {"context": retrieval_chain_rag_fusion,
         "question": itemgetter("question")}
        | prompt
        | llm
        | StrOutputParser()
)
