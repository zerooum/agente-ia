from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm

root_agent = Agent(
    name="meu_agente2",
    instruction="""
        Você é um especialista em python
        Você ajuda programadores a criar e debugar codigo python
    """,
    # model="gemini-2.5-flash-lite"
    model=LiteLlm(model="anthropic/claude-sonnet-4-6")
    )