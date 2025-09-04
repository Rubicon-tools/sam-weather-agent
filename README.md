# Weather Agent (SAM Project)

This project is a Python-based agent built with Solace Agent Mesh (SAM).  
It provides a weather service API and integrates with Solace messaging.


## Requirements
- Python 3.10+
- Docker (optional, for running inside container)
- [Solace Agent Mesh](https://github.com/SolaceProducts/solace-agent-mesh) 

    ```bash
    uv venv .venv
    ```
    
    ```bash
    source .venv/bin/activate   # Linux/Mac
    .venv\Scripts\activate      # Windows
    ```
    
     ```bash
    uv pip install solace-agent-mesh
    ```

## Setup

Clone the repository:
```bash
git clone https://github.com/Rubicon-tools/sam-weather-agent
cd sam-weather-agent
```



Make sure your .env file is configured correctly

## run - Run the SAM Application

```bash
sam run
```

## Running Agent
For debugging or isolated development testing, you can run your agent from the src directory directly using the SAM CLI.
```bash
cd src
sam run ../config.yaml
```

## Interacting with SAM
To access the browser UI, navigate to http://localhost:8000 in your web browser. If you specified a different port during the init step, use that port instead. For Docker deployments with custom port mappings (using the -p flag), use the host port specified in your port mapping configuratio

Logs will be written to weather-agent.log.

## Notes

The repository includes .gitignore to exclude unnecessary files and folders such as logs, .venv, and compiled Python files.

Configuration files are stored under the configs/ folder.
