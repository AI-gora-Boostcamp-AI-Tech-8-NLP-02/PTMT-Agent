from langchain_core.prompts import ChatPromptTemplate

CONCEPT_EXPANSION_PROMPT_V4 = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert AI research assistant specializing in designing personalized learning curricula and concept structures. "
        "You analyze the given keyword graph to determine whether any essential concepts are missing in the learning flow, "
        "and you add new concepts only when strictly necessary. "
        "When required, you must use the provided tool (web search) to verify prerequisite relationships or conceptual dependencies between concepts. "
        "You must strictly follow all instructions and output results in JSON format only."
    ),
    (
        "human",
        """
        Below is the current learning keyword graph.
        Based on this graph, determine whether additional concepts are required
        to improve the learning flow.

        ### Target Paper
        {paper_info}
        
        ### User Level
        {user_level}

        ### Concepts Already Known by the User
        {known_concept}

        ### Current Keyword Graph (JSON)
        {keyword_graph}

        ### Reason for Concept Expansion Request
        {reason}
        
        ### List of Keyword IDs That May Require Supplementation
        {keyword_ids}

        ---
        
        ## Concept Expansion Strategy by User Level

        ### novice
        - Ensure sufficient depth in the learning graph.
        - You may include high-level domain concepts or broad category concepts related to the target paper.
        - Actively add intuitive and foundational concepts that precede formulas or algorithms.

        ### intermediate
        - Maintain a moderate depth in the learning graph.
        - Add only concepts that directly help with implementation, mathematical understanding,
          or comprehension of algorithmic structure.

        ### expert
        - Do NOT add high-level domain concepts or general concepts that are not directly related to the target paper.
        - Concepts must focus on paper-level details such as specific mechanisms,
          theoretical assumptions, or subtle distinctions.
          
        ---
        ## How to Use the Expansion Reason
        - The provided reason explains why concept expansion was requested and may suggest specific missing concepts or learning gaps.
        - You MUST consider this reason when deciding whether to add new concepts. However, the reason is NOT a hard constraint.
        
        You MAY add concepts that are NOT explicitly mentioned in the reason
        if and only if:
        - They are necessary to improve the learning flow toward the target paper, AND
        - They comply with the user's level ({user_level}), AND
        - They do NOT violate any rules regarding concepts already known by the user.

        ---
        ## Rules Regarding Concepts Already Known by the User

        If any of the following conditions apply, the concept must NOT be added as a node:
        - The concept is identical to a concept included in {known_concept}
        - The concept is a synonym, abbreviation, full form, or variant expression of a concept in {known_concept}
        - The concept is a sub-concept of a concept in {known_concept}

        Any newly added concept must:
        - Have independent meaning without relying on {known_concept}, and
        - Provide a clear increase in information necessary for understanding the target paper.

        ---
        ## Common Rules

        - Keywords must be written as English words or short phrases.
        - Do NOT add keywords that are merely generalized versions of concepts already in the graph.
        - Never re-output existing nodes or edges from the current keyword graph.
        - Never output concepts that are identical or highly similar to concepts already known by the user.
        - Output only concepts that you determine truly need to be added.
        - Every new node must be connected by at least one edge to an existing keyword,
          the target paper, or another newly added keyword.
        - All edges must be connected using keyword_id values.
        - If you create a prerequisite (PREREQ) relationship between keywords,
          you MUST use the tool (web search) to verify the relationship before creating the edge.
          (Briefly state the reason for the prerequisite relationship in the edge's reason field.)
        - If you determine that no additional concepts are required,
          output empty arrays for both nodes and edges.

        ---
        ## Output Format (Must Be Followed Exactly)

        Do NOT include explanations, comments, markdown, or code blocks (```).
        Output must be in the following JSON format ONLY:

        {{
          "expanded_graph": {{
            "nodes": [
              {{
                "keyword_id": string,
                "keyword": string
              }}
            ],
            "edges": [
              {{
                "start": string,
                "end": string,
                "reason": string
              }}
            ]
          }}
        }}
        """
    )
])
