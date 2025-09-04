"""
Weather agent tools for fetching and processing weather data.
"""

import json
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from solace_ai_connector.common.log import log
from solace_agent_mesh.agent.utils.artifact_helpers import save_artifact_with_metadata

async def get_current_weather(
    location: str,
    units: str = "metric",
    save_to_file: bool = False,
    tool_context: Optional[ToolContext] = None,
    tool_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get current weather conditions for a specified location.
    
    Args:
        location: City name, state, and country (for example, "New York, NY, US")
        units: Temperature units - "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin"
        save_to_file: Whether to save the weather report as an artifact
    
    Returns:
        Dictionary containing current weather information
    """
    log_identifier = "[GetCurrentWeather]"
    log.info(f"{log_identifier} Getting current weather for: {location}")
    
    if not tool_context:
        return {
            "status": "error",
            "message": "Tool context is required for weather operations"
        }
    
    try:
        # Get weather service from agent state
        host_component = getattr(tool_context._invocation_context, "agent", None)
        if host_component:
            host_component = getattr(host_component, "host_component", None)
        
        if not host_component:
            return {
                "status": "error",
                "message": "Could not access agent host component"
            }
        
        weather_service = host_component.get_agent_specific_state("weather_service")
        if not weather_service:
            return {
                "status": "error",
                "message": "Weather service not initialized"
            }
        
        # Fetch weather data
        weather_data = await weather_service.get_current_weather(location, units)
        
        # Create human-readable summary
        summary = _create_weather_summary(weather_data)
        
        result = {
            "status": "success",
            "location": weather_data["location"],
            "summary": summary,
            "data": weather_data
        }
        
        # Save to artifact if requested
        if save_to_file:
            artifact_result = await _save_weather_artifact(
                weather_data, f"current_weather_{location}", tool_context
            )
            result["artifact"] = artifact_result
        
        log.info(f"{log_identifier} Successfully retrieved weather for {location}")
        return result
    
    except ValueError as e:
        log.warning(f"{log_identifier} Invalid location: {e}")
        return {
            "status": "error",
            "message": f"Location error: {str(e)}"
        }
    except Exception as e:
        log.error(f"{log_identifier} Error getting weather: {e}")
        return {
            "status": "error",
            "message": f"Weather service error: {str(e)}"
        }


async def get_weather_forecast(
    location: str,
    days: int = 5,
    units: str = "metric",
    save_to_file: bool = False,
    tool_context: Optional[ToolContext] = None,
    tool_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get weather forecast for a specified location.
    
    Args:
        location: City name, state, and country
        days: Number of days for forecast (1-5)
        units: Temperature units
        save_to_file: Whether to save the forecast as an artifact
    
    Returns:
        Dictionary containing weather forecast information
    """
    log_identifier = "[GetWeatherForecast]"
    log.info(f"{log_identifier} Getting {days}-day forecast for: {location}")
    
    if not tool_context:
        return {
            "status": "error",
            "message": "Tool context is required for weather operations"
        }
    
    # Validate days parameter
    if not 1 <= days <= 5:
        return {
            "status": "error",
            "message": "Days must be between 1 and 5"
        }
    
    try:
        # Get weather service from agent state
        host_component = getattr(tool_context._invocation_context, "agent", None)
        if host_component:
            host_component = getattr(host_component, "host_component", None)
        
        if not host_component:
            return {
                "status": "error",
                "message": "Could not access agent host component"
            }
        
        weather_service = host_component.get_agent_specific_state("weather_service")
        if not weather_service:
            return {
                "status": "error",
                "message": "Weather service not initialized"
            }
        
        # Fetch forecast data
        forecast_data = await weather_service.get_weather_forecast(location, days, units)
        
        # Create human-readable summary
        summary = _create_forecast_summary(forecast_data)
        
        result = {
            "status": "success",
            "location": forecast_data["location"],
            "summary": summary,
            "data": forecast_data
        }
        
        # Save to artifact if requested
        if save_to_file:
            artifact_result = await _save_weather_artifact(
                forecast_data, f"forecast_{location}_{days}day", tool_context
            )
            result["artifact"] = artifact_result
        
        log.info(f"{log_identifier} Successfully retrieved forecast for {location}")
        return result
    
    except ValueError as e:
        log.warning(f"{log_identifier} Invalid location: {e}")
        return {
            "status": "error",
            "message": f"Location error: {str(e)}"
        }
    except Exception as e:
        log.error(f"{log_identifier} Error getting forecast: {e}")
        return {
            "status": "error",
            "message": f"Weather service error: {str(e)}"
        }


def _create_weather_summary(weather_data: Dict[str, Any]) -> str:
    """Create a human-readable weather summary."""
    temp_unit = "°C"  # Assuming metric units for summary
    
    summary = f"Current weather in {weather_data['location']}:\n"
    summary += f"• Temperature: {weather_data['temperature']}{temp_unit} (feels like {weather_data['feels_like']}{temp_unit})\n"
    summary += f"• Conditions: {weather_data['description']}\n"
    summary += f"• Humidity: {weather_data['humidity']}%\n"
    summary += f"• Wind: {weather_data['wind_speed']} m/s\n"
    summary += f"• Visibility: {weather_data['visibility']} km"
    
    return summary


def _create_forecast_summary(forecast_data: Dict[str, Any]) -> str:
    """Create a human-readable forecast summary."""
    summary = f"Weather forecast for {forecast_data['location']}:\n\n"
    
    for forecast in forecast_data['forecasts']:
        date = datetime.fromisoformat(forecast['date']).strftime('%A, %B %d')
        summary += f"• {date}: {forecast['description']}\n"
        summary += f"  High: {forecast['temperature_max']:.1f}°C, Low: {forecast['temperature_min']:.1f}°C\n"
        if forecast['precipitation_probability'] > 0:
            summary += f"  Precipitation: {forecast['precipitation_probability']:.0f}% chance\n"
        summary += "\n"
    
    return summary.strip()


async def _save_weather_artifact(
    weather_data: Dict[str, Any],
    filename_base: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Save weather data as an artifact."""
    try:
        # Prepare content
        content = json.dumps(weather_data, indent=2, default=str)
        timestamp = datetime.now(timezone.utc)
        filename = f"{filename_base}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Save artifact
        artifact_service = tool_context._invocation_context.artifact_service
        result = await save_artifact_with_metadata(
            artifact_service=artifact_service,
            app_name=tool_context._invocation_context.app_name,
            user_id=tool_context._invocation_context.user_id,
            session_id=tool_context._invocation_context.session.id,
            filename=filename,
            content_bytes=content.encode('utf-8'),
            mime_type="application/json",
            metadata_dict={
                "description": "Weather data report",
                "source": "Weather Agent"
            },
            timestamp=timestamp
        )
        
        return {
            "filename": filename,
            "status": result.get("status", "success")
        }
    
    except Exception as e:
        log.error(f"[WeatherArtifact] Error saving artifact: {e}")
        return {
            "status": "error",
            "message": f"Failed to save artifact: {str(e)}"
        }