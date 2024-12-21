from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END
from langgraph.graph import MessagesState
from langgraph.types import Command

from agents.analyze_agent import analyze_graph
from agents.knowledge_agent import final_rag_chain


def communication_agent(state: MessagesState) -> Command[Literal["knowledge_agent", END]]:
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and "analyze" in last_message.content:
        print("Final result sent to user:", last_message.content)
    else:
        # system_prompt = "You are the Communication Agent. Forward the user's query to the Knowledge Agent and return the response to the user."
        # messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        # response = llm.invoke(messages)
        return Command(
            goto="knowledge_agent",
            update={"messages": state["messages"]}
        )


def knowledge_agent(state: MessagesState) -> Command[Literal["analyze_agent"]]:
    user_query = state["messages"][-1].content
    print(user_query)
    answer = final_rag_chain.invoke({"question": user_query})
    # Return the answer to the Communication Agent
    print(answer)
    return Command(
        goto="analyze_agent",
        update={"messages": [{"role": "assistant", "content": answer}]}
    )


def analyze_agent(state: MessagesState) -> Command[Literal["communication_agent"]]:
    input_text = state["messages"][-1].content

    analyzed_result = analyze_graph.invoke({"messages": [("user", input_text)]})

    # if isinstance(analyzed_result, dict):
    #     analyzed_output = str(analyzed_result)
    # elif isinstance(analyzed_result, str):
    #     analyzed_output = analyzed_result
    # else:
    #     raise ValueError("Analyze agent received an invalid response format.")
    #
    return Command(
        goto="communication_agent",
        update={"messages": [{"role": "assistant", "content": f"analyze: {analyzed_result['messages'][-1].content}"}]}
    )


from langgraph.graph import StateGraph, START

builder = StateGraph(MessagesState)
builder.add_node("communication_agent", communication_agent)
builder.add_node("knowledge_agent", knowledge_agent)
builder.add_node("analyze_agent", analyze_agent)
builder.add_edge(START, "communication_agent")

graph = builder.compile()
#
# from IPython.display import display, Image
#
# display(Image(graph.get_graph().draw_mermaid_png()))
