import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from . import tools, config_loader

load_dotenv()

def get_llm(llm_config: dict):
    provider = llm_config.get("provider", "").lower()
    model_name = llm_config.get("model_name")
    temperature = llm_config.get("temperature", 0.0)

    if provider == "google":
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    elif provider == "ollama":
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model=model_name,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def create_agent_executor(agent_name: str):
    config = config_loader.load_config(agent_name)
    
    available_tools = [getattr(tools, tool_name) for tool_name in config.get("tools", [])]

    llm = get_llm(config.get("llm", {}))
    llm_with_tools = llm.bind_tools(tools=available_tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", config.get("prompt_template", "You are a helpful assistant.")),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(llm_with_tools, available_tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=available_tools, verbose=True)
    
    return agent_executor

def invoke_agent(agent_name: str, query: str) -> str:
    agent_executor = create_agent_executor(agent_name)
    response = agent_executor.invoke({"input": query})
    return response.get("output", "Could not process the request.")
