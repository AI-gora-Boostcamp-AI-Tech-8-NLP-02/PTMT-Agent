from langchain_core.messages import AIMessage

def get_last_ai_message(response: dict) -> AIMessage:
    for msg in reversed(response["messages"]):
        if isinstance(msg, AIMessage):
            return msg
    raise ValueError("No AIMessage found in response")
