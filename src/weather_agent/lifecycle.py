"""
Lifecycle functions for the Weather Agent.
"""

from typing import Any
import asyncio
from pydantic import BaseModel, Field, SecretStr
from solace_ai_connector.common.log import log
from .services.weather_service import WeatherService


class WeatherAgentInitConfig(BaseModel):
    """
    Configuration model for Weather Agent initialization.
    """
    api_key: SecretStr = Field(description="OpenWeatherMap API key")
    base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="Weather API base URL"
    )
    startup_message: str = Field(
        default="Weather Agent is ready to provide weather information!",
        description="Message to log on startup"
    )


def initialize_weather_agent(host_component: Any, init_config: WeatherAgentInitConfig):
    """
    Initialize the Weather Agent with weather service.
    
    Args:
        host_component: The agent host component
        init_config: Validated initialization configuration
    """
    log_identifier = f"[{host_component.agent_name}:init]"
    log.info(f"{log_identifier} Starting Weather Agent initialization...")
    
    try:
        # Initialize weather service
        weather_service = WeatherService(
            api_key=init_config.api_key.get_secret_value(),
            base_url=init_config.base_url
        )
        
        # Store service in agent state
        host_component.set_agent_specific_state("weather_service", weather_service)
        
        # Log startup message
        log.info(f"{log_identifier} {init_config.startup_message}")
        
        # Store initialization metadata
        host_component.set_agent_specific_state("initialized_at", "2024-01-01T00:00:00Z")
        host_component.set_agent_specific_state("weather_requests_count", 0)
        
        log.info(f"{log_identifier} Weather Agent initialization completed successfully")
    
    except Exception as e:
        log.error(f"{log_identifier} Failed to initialize Weather Agent: {e}")
        raise


def cleanup_weather_agent(host_component: Any):
    """
    Clean up Weather Agent resources.
    
    Args:
        host_component: The agent host component
    """
    log_identifier = f"[{host_component.agent_name}:cleanup]"
    log.info(f"{log_identifier} Starting Weather Agent cleanup...")

    async def cleanup_async(host_component: Any):
        try:
            # Get and close weather service
            weather_service = host_component.get_agent_specific_state("weather_service")
            if weather_service:
                await weather_service.close()
                log.info(f"{log_identifier} Weather service closed successfully")
            
            # Log final statistics
            request_count = host_component.get_agent_specific_state("weather_requests_count", 0)
            log.info(f"{log_identifier} Agent processed {request_count} weather requests during its lifetime")
            
            log.info(f"{log_identifier} Weather Agent cleanup completed")
        
        except Exception as e:
            log.error(f"{log_identifier} Error during cleanup: {e}")
    
    # run cleanup in the event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cleanup_async(host_component))
    log.info(f"{log_identifier} Weather Agent cleanup completed successfully")