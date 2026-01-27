from typing import List, Dict, Any, TypedDict

class OrchestratorDecision(TypedDict):
    tasks:List[str]
    is_keyword_sufficient: bool      
    is_resource_sufficient: bool                    
    needs_description_ids: List[str]    
    insufficient_resource_ids: List[str] 
    missing_concepts: List[str]          
    keyword_reasoning:str
    resource_reasoning:str                  




    
    
    