import os
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage

load_dotenv()

def get_solar_model(model_name: str = "solar-pro2", temperature: float = 0.7):
    api_key = os.environ.get("UPSTAGE_API_KEY")
    
    return ChatUpstage(
        model=model_name,
        temperature=temperature,
        upstage_api_key=api_key
    )