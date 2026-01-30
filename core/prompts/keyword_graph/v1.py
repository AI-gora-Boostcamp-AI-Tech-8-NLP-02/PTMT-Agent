from langchain_core.prompts import ChatPromptTemplate

KEYWORD_GRAPH_PROMPT_V1 = ChatPromptTemplate.from_messages([
    ("system", "You are a keyword graph generator."),
    ("user", "{paper_info}")
])
