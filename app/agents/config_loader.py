import yaml
import os
import re
from pathlib import Path
from typing import Optional

def load_config(agent_name: str, base_path: Optional[Path] = None) -> dict:
    """
    Loads a YAML configuration file for an agent, substituting environment variables.
    An optional base_path can be provided for testing purposes.
    """
    if base_path is None:
        base_path = Path(__file__).parent

    config_path = base_path / "configs" / f"{agent_name}.yaml"
    
    if not config_path.is_file():
        raise FileNotFoundError(f"Agent configuration file not found at {config_path}")

    env_var_pattern = re.compile(r'\$\{(.*?)\}')
    
    with open(config_path, 'r') as f:
        raw_content = f.read()

    placeholders = env_var_pattern.findall(raw_content)
    for placeholder in placeholders:
        env_value = os.getenv(placeholder)
        if env_value is None:
            if placeholder == "GOOGLE_MODEL" and os.getenv("LLM_PROVIDER", "").lower() == "ollama":
                env_value = os.getenv("OLLAMA_MODEL")
            
            if env_value is None:
                raise ValueError(f"Environment variable '{placeholder}' not found and is required.")
        
        raw_content = raw_content.replace(f'${{{placeholder}}}', env_value)
            
    loaded_yaml = yaml.safe_load(raw_content)
    if loaded_yaml is None:
        return {}
    return loaded_yaml
