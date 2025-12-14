"""
Utility module for loading and accessing configuration files.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """Loads and manages configuration from YAML files."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self.agents_config: Dict[str, Any] = {}
        
        # Load environment variables from .env file (don't override existing env vars)
        load_dotenv(override=False)
        
        # Load configurations
        self._load_main_config()
        self._load_agents_config()
    
    def _load_main_config(self):
        """Load the main configuration file."""
        config_path = self.config_dir / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    def _load_agents_config(self):
        """Load additional agents configuration."""
        agents_path = self.config_dir / "agents.yaml"
        if agents_path.exists():
            with open(agents_path, 'r', encoding='utf-8') as f:
                additional_agents = yaml.safe_load(f) or {}
                # Merge with main config agents
                if 'agents' in additional_agents:
                    if 'agents' not in self.config:
                        self.config['agents'] = {}
                    self.config['agents'].update(additional_agents['agents'])
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'llm.model')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        return self.config.get('llm', {})
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration or None
        """
        agents = self.config.get('agents', {})
        return agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all agent configurations."""
        return self.config.get('agents', {})
    
    def get_rag_config(self) -> Dict[str, Any]:
        """Get RAG configuration."""
        return self.config.get('rag', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.config.get('ui', {})
    
    def get_deployment_config(self) -> Dict[str, Any]:
        """Get deployment configuration."""
        return self.config.get('deployment', {})
    
    def get_evaluation_config(self) -> Dict[str, Any]:
        """Get evaluation configuration."""
        return self.config.get('evaluation', {})
    
    def get_env_variable(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)
    
    def get_api_key(self, key_env_name: str) -> str:
        """
        Get API key from environment variables.
        
        Args:
            key_env_name: Environment variable name for the API key
            
        Returns:
            API key value
            
        Raises:
            ValueError: If API key not found
        """
        api_key = os.getenv(key_env_name)
        if not api_key:
            raise ValueError(
                f"API key not found. Please set {key_env_name} environment variable"
            )
        return api_key


# Global configuration instance
_config_instance: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    Get the global configuration instance.
    
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader()
    return _config_instance


def reload_config():
    """Reload the configuration from files."""
    global _config_instance
    _config_instance = ConfigLoader()
