from langchain_core.prompts import ChatPromptTemplate

FIRST_CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research assistant specializing in the analysis of AI research papers. "
        "Your goal is to accurately identify the paper’s core contributions and research objectives. "
        "You must strictly follow all instructions and output results in JSON format only.\n"
        "Below is the full content of a single AI research paper. "
        "Summarize the paper so that its main contributions and research goals are clearly reflected, "
        "and extract 3–5 **core concepts** that best represent the paper.\n"
        "### Extraction Guidelines\n"
        "- paper_summary MUST be written in Korean\n"
        "- paper_concepts MUST be written as English words or short phrases"
    ),
    (
        "human",
        """
        ### Paper Title
        {paper_name}

        ### Paper Content
        #### Abstract
        {paper_abstract}
        
        #### Body
        {paper_body}

        The above content represents the full text of an AI research paper.
        Summarize the paper so that its core contributions and research objectives are clearly conveyed,
        and extract 3–5 **core concepts** that best represent the paper.

        ### Extraction Guidelines
        - paper_summary MUST be written in Korean
        - paper_concepts MUST be written as English words or short phrases

        You MUST output ONLY the following JSON format.
        Do NOT include explanations, comments, markdown, or code blocks (```).

        {{
            "paper_summary": string,
            "paper_concepts": string[]
        }}
        """
    )
])

FINAL_CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert research assistant specializing in the analysis of AI research papers. "
        "Your role is to select clear, single-concept terms."
        "You must strictly follow all instructions and output results in JSON format only.\n"
        "Below is information about a single AI research paper. "
        "Extract the **core prerequisite concepts** that a user must learn in advance in order to understand this paper. "
        "You must comprehensively consider the following information:\n"
        "- The paper’s topic and research objectives\n"
        "- The initially extracted core concepts representing the paper\n"
        
        "### Extraction Criteria\n"
        "- Each concept must be necessary to understand the paper\n"
        "- Merge concepts with overlapping meanings into a single concept\n"
        "- Limit the final number of concepts to 3–5\n"
        "- All concepts must be output in English\n"
        "- Each item must be a **single noun or noun phrase that could serve as a Wikipedia article title**\n"
        "- Wikipedia article titles are provided **for reference only**, to guide naming, normalization, and the expected level of abstraction."
        "- Do NOT treat Wikipedia titles as a required list or as candidates that must be selected."
        "- A concept may be included even if it does NOT exactly match any Wikipedia title, as long as it represents a clear, single prerequisite concept."
        "- Explanatory sentences, formulas, compound expressions, or descriptive phrases are strictly prohibited\n"
        "- Remove unnecessary adjectives or modifiers and normalize each concept to its most fundamental form"
    ),
    (
        "human",
        """
        ### Paper Title
        {paper_name}
        
        ### Paper Summary
        {paper_summary}

        ### Paper Content
        #### Abstract
        {paper_abstract}
        
        #### Body
        {paper_body}
        
        ### Initial Core Concepts (Paper-Representative Concepts)
        {initial_concepts}
        
        ### Related Wikipedia Article Titles
        {wiki_words}

        The above is information about a single AI research paper.
        Extract the **core prerequisite concepts** that a user must learn in advance in order to understand this paper.
        You must comprehensively consider the following information:\n
        - The paper’s topic and research objectives\n
        - The initially extracted core concepts representing the paper\n
        
        ### Extraction Criteria\n
        - Each concept must be necessary to understand the paper\n
        - Merge concepts with overlapping meanings into a single concept\n
        - Limit the final number of concepts to 3–5\n
        - All concepts must be output in English\n
        - Each item must be a **single noun or noun phrase that could serve as a Wikipedia article title**\n
        - Wikipedia article titles are provided **for reference only**, to guide naming, normalization, and the expected level of abstraction.
        - Do NOT treat Wikipedia titles as a required list or as candidates that must be selected.
        - A concept may be included even if it does NOT exactly match any Wikipedia title, as long as it represents a clear, single prerequisite concept.
        - Explanatory sentences, formulas, compound expressions, or descriptive phrases are strictly prohibited\n
        - Remove unnecessary adjectives or modifiers and normalize each concept to its most fundamental form"

        You MUST output ONLY the following JSON format.
        Do NOT include explanations, comments, markdown, or code blocks (```).

        {{
            "paper_concepts": string[]
        }}
        """
    )
])
