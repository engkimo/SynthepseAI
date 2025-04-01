# SynthepseAI Agent

## Overview

SynthepseAI Agent is an autonomous AI agent system with self-correction capabilities. Simply by setting a goal, the agent automatically plans and executes tasks while learning from and correcting errors to achieve the objective. It is built on an extended version of the manus architecture and incorporates a learning system utilizing GraphRAG, enabling continuous improvement based on experience. The system now supports the LLLM (Larger LLM) concept, integrating multiple advanced technologies to create a more powerful and autonomous AI ecosystem.

### Key Features

- **Automated Task Planning and Execution**: Decomposes complex goals into smaller tasks and automatically generates and executes Python code for each task.
- **Self-Correction Ability**: Detects errors during execution and attempts to automatically correct them.
- **Learning from Experience**: Learns from past error patterns and successful code implementations to apply to new tasks.
- **Module Reuse**: Extracts reusable modules from successful code to utilize in new tasks.
- **Isolated Execution Environments**: Each project runs in its own virtual environment to prevent dependency conflicts.
- **Local Model Support**: Runs with local LLM models (default: Microsoft Phi-2) using MPS acceleration on Mac, eliminating the need for API keys.
- **Knowledge Editing (ROME)**: Directly edits the internal knowledge of language models using Rank-One Model Editing technology.
- **Self-Reflection Reasoning (COAT)**: Implements Chain-of-Action-Thought methodology for enhanced error detection and self-correction.
- **Knowledge Graph Processing (R-GCN)**: Utilizes Relational Graph Convolutional Networks to process and reason with complex knowledge graphs.

## System Requirements

### Mandatory Environment
- Python 3.9 or higher
- SQLite 3.x
- Docker (required when using Weaviate)
- PyTorch with MPS support (for Mac users with Apple Silicon)

### Dependencies
```bash
torch>=2.0.0
transformers>=4.30.0
scipy>=1.9.0
networkx>=3.0
dgl>=1.0.0
openai>=1.0.0
weaviate-client>=3.15.0
tenacity>=8.0.0
python-dotenv>=1.0.0
sqlite3
accelerate>=0.20.0
```

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/SynthepseAI.git
cd SynthepseAI
```

### 2. Set Up the Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file and include the following:
```dotenv
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo
```

### 5. Set Up Weaviate (for GraphRAG)
```bash
docker-compose -f docker-compose.yml up -d
```

## Usage

### Basic Execution

```bash
# Run with a specified goal
python main.py --goal "Create a CSV file, perform data analysis, and generate graphs for the results"

# Run with a specified workspace directory
python main.py --goal "Perform web scraping to collect data" --workspace ./custom_workspace

# Run in debug mode
python main.py --goal "Process a text file and compute statistics" --debug
```

### Using Local Models

By default, SynthepseAI now uses the Microsoft Phi-2 local model with MPS acceleration on Mac:

```bash
# Run with local model (default)
python main.py --goal "Analyze this dataset and create visualizations"

# Configure local model options in config.json
# {
#   "use_local_model": true,
#   "local_model_name": "microsoft/phi-2",
#   "device": "mps"  # Uses MPS acceleration on Mac
# }
```

To use OpenAI API instead:

```bash
# Run with OpenAI API
python main.py --goal "Summarize these documents" --use-api
```

### Example Runs

```bash
# Execute a sample task
python example.py

# Run LLLM technology demonstrations
python examples/example_local_model_phi2.py  # Local model with MPS
python examples/example_rome_local_model.py  # ROME knowledge editing
python examples/example_coat_local_model.py  # COAT self-correction
python examples/example_rgcn_local_model.py  # R-GCN knowledge graph
python examples/example_lllm_integrated.py   # Full LLLM integration
```

### Enabling the Learning Feature

```bash
# Enable learning using GraphRAG
python main.py --goal "Extract text from image files" --weaviate-url "http://localhost:8080"
```

## Project Structure

```
SynthepseAI/
├── main.py                    # Main entry point
├── example.py                 # Sample execution script
├── config.json                # Configuration file
├── requirements.txt           # Dependency list
├── docker-compose.yml         # Weaviate configuration file
├── core/                      # Core modules
│   ├── auto_plan_agent.py     # Self-correcting agent with COAT integration
│   ├── base_agent.py          # Base agent
│   ├── base_flow.py           # Base flow
│   ├── coat_reasoner.py       # COAT reasoning implementation
│   ├── graph_rag_manager.py   # GraphRAG manager
│   ├── llm.py                 # LLM integration with local model support
│   ├── local_model_manager.py # Local model management with MPS support
│   ├── modular_code_manager.py # Module manager
│   ├── planning_flow.py       # Planning flow
│   ├── project_environment.py # Project environment
│   ├── rgcn_processor.py      # R-GCN knowledge graph processor
│   ├── rome_model_editor.py   # ROME model editing implementation
│   ├── script_templates.py    # Script templates
│   ├── task_database.py       # Task database
│   ├── tool_agent.py          # Tool agent
│   └── tools/                 # Tool modules
│       ├── base_tool.py       # Base tool
│       ├── file_tool.py       # File operations
│       ├── package_manager.py # Package management
│       ├── planning_tool.py   # Planning tool
│       ├── python_execute.py  # Python execution
│       ├── python_project_execute.py # Project environment execution
│       ├── docker_execute.py  # Docker execution
│       └── system_tool.py     # System operations
├── examples/                  # Example demonstrations
│   ├── example_coat.py        # COAT demonstration
│   ├── example_coat_local_model.py # COAT with local model
│   ├── example_lllm_integrated.py # Integrated LLLM demonstration
│   ├── example_local_model_phi2.py # Phi-2 local model demo
│   ├── example_rgcn.py        # R-GCN demonstration
│   ├── example_rgcn_local_model.py # R-GCN with local model
│   ├── example_rome.py        # ROME demonstration
│   └── example_rome_local_model.py # ROME with local model
├── tests/                     # Test suite
│   ├── integration_test_basic_functionality.py # Basic integration tests
│   ├── integration_test_coat.py # COAT integration tests
│   ├── integration_test_rgcn.py # R-GCN integration tests
│   ├── integration_test_rome.py # ROME integration tests
│   ├── regression_test_basic_tasks.py # Regression tests
│   ├── test_coat_reasoner.py  # COAT unit tests
│   ├── test_llm_local_model.py # Local model unit tests
│   ├── test_local_model_manager.py # Local model manager tests
│   ├── test_rgcn_processor.py # R-GCN unit tests
│   ├── test_rgcn_processor_mps.py # R-GCN MPS tests
│   ├── test_rome_model_editor.py # ROME unit tests
│   └── test_rome_model_editor_mps.py # ROME MPS tests
└── workspace/                 # Working directory
    ├── modules/               # Reusable modules
    └── project_{plan_id}/     # Project environment
        ├── venv/              # Virtual environment
        ├── task_{task_id}.py  # Task script
        ├── requirements.txt   # Dependencies
        └── installed_packages.json # Installed packages
```

## Architecture and Design Philosophy

SynthepseAI Agent is composed of the following main components:

### System Architecture Overview

```mermaid
flowchart TD
    title[SynthepseAI System Architecture]
    
    %% Main Systems
    UserInput[User Input]
    ExtSvc[External Services]
    FlowSys[Flow System]
    AgentSys[Agent System]
    ToolSys[Tool System]
    
    %% Connections
    UserInput --> FlowSys
    ExtSvc --> FlowSys
    FlowSys --> AgentSys
    AgentSys --> ToolSys
    ToolSys --> ExtSvc
    
    %% Styling
    classDef default fill:#f0f0ff,stroke:#333,stroke-width:1px
    classDef title fill:none,stroke:none,color:#333,font-size:18px
    
    class title title
```

### Basic Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant Main
    participant SynthepseAI
    participant LLM
    participant Tools
    
    User->>Main: Input Prompt
    Main->>SynthepseAI: run(prompt)
    
    rect rgb(240, 240, 255)
        Note over SynthepseAI,LLM: Loop [Until max steps]
        SynthepseAI->>LLM: Execute Step
        LLM-->>SynthepseAI: Next Action
        
        alt Tool Execution
            SynthepseAI->>Tools: Tool Invocation
            Tools-->>SynthepseAI: Result
        end
    end
    
    SynthepseAI->>SynthepseAI: Generate Response
    SynthepseAI-->>Main: Final Result
    Main-->>User: Output
```

### Planning Flow

```mermaid
sequenceDiagram
    participant User
    participant PlanningFlow
    participant PlanningTool
    participant Executor
    participant LLM
    
    User->>PlanningFlow: execute(input_text)
    PlanningFlow->>PlanningTool: Create Plan
    PlanningTool-->>PlanningFlow: Plan Information
    
    rect rgb(240, 240, 255)
        Note over PlanningFlow,LLM: Loop [For each step]
        PlanningFlow->>PlanningFlow: Get Current Step Info
        PlanningFlow->>Executor: Execute Step
        Executor->>LLM: Execute Task
        LLM-->>Executor: Result
        Executor-->>PlanningFlow: Execution Result
        PlanningFlow->>PlanningTool: Mark Step Complete
    end
    
    PlanningFlow->>PlanningFlow: Process Plan Completion
    PlanningFlow-->>User: Final Result
```

### Class Structure

```mermaid
classDiagram
    class BaseFlow {
        +agents: Dict[str, BaseAgent]
        +primary_agent_key: str
        +primary_agent: BaseAgent
        +execute(input_text: str) : str
        +get_agent(key: str) : BaseAgent
        +add_agent(key: str, agent: BaseAgent) : void
    }
    
    class PlanningFlow {
        +llm: LLM
        +planning_tool: PlanningTool
        +executor_keys: List[str]
        +active_plan_id: str
        +current_step_index: int
        +execute(input_text: str) : str
        +get_executor(step_type: str) : BaseAgent
    }
    
    class BaseAgent {
        +name: str
        +description: str
        +system_prompt: str
        +next_step_prompt: str
        +llm: LLM
        +memory: Memory
        +state: AgentState
        +run(request: str) : str
        +step() : str
    }
    
    class ToolCallAgent {
        +available_tools: ToolCollection
        +step() : str
        +handle_tool_calls(tool_calls) : str
    }
    
    class SynthepseAI {
        +name: str = "SynthepseAI"
        +description: str
        +system_prompt: str
        +next_step_prompt: str
        +available_tools: ToolCollection
    }
    
    class BaseTool {
        +name: str
        +description: str
        +parameters: dict
        +execute(**kwargs) : Any
        +to_param() : Dict
    }
    
    class PlanningTool {
        +name: str = "planning"
        +description: str
        +parameters: dict
        +plans: dict
        +_current_plan_id: str
        +execute(command, plan_id, ...) : ToolResult
    }
    
    BaseFlow <|-- PlanningFlow
    BaseAgent <|-- ToolCallAgent
    ToolCallAgent <|-- SynthepseAI
    BaseTool <|-- PlanningTool
    
    PlanningFlow --> BaseAgent
    ToolCallAgent --> BaseTool
```

### Agent Execution System

```mermaid
flowchart TD
    UserInput[User Input] --> Agent[Agent]
    
    Agent --> ActionDecision{Action Decision}
    
    ActionDecision -->|Tool Execution| ToolInvocation[Tool Invocation]
    ActionDecision -->|Direct Response| ResponseGen[Response Generation]
    
    ToolInvocation --> ToolCall[Tool Call]
    ToolCall --> ResultProc[Result Processing]
    
    ResultProc --> Agent
    ResponseGen --> FinalResponse[Final Response]
    
    %% Styling
    classDef default fill:#f0f0ff,stroke:#333,stroke-width:1px
    classDef decision fill:#f5f5ff,stroke:#333,stroke-width:1px,shape:diamond
    
    class ActionDecision decision
```

### Planning System

```mermaid
flowchart TD
    UserReq[User Request] --> PlanCreation[Plan Creation]
    PlanCreation --> StepList[Step List Creation]
    StepList --> GetCurrent[Get Current Step]
    
    GetCurrent --> AgentSelect[Select Appropriate Agent]
    AgentSelect --> ExecStep[Execute Step]
    
    ExecStep --> Complete{Completed?}
    Complete -->|No| GetCurrent
    Complete -->|Yes| FinalResult[Generate Final Result]
    
    %% Styling
    classDef default fill:#f0f0ff,stroke:#333,stroke-width:1px
    classDef decision fill:#f5f5ff,stroke:#333,stroke-width:1px,shape:diamond
    
    class Complete decision
```

### Tool Integration System

```mermaid
flowchart TD
    Agent[Agent] --> ToolColl[Tool Collection]
    
    ToolColl --> ToolSelect{Tool Selection}
    
    ToolSelect --> PythonExec[Python Execution]
    ToolSelect --> WebBrowsing[Web Browsing]
    ToolSelect --> GoogleSearch[Google Search]
    ToolSelect --> FileOps[File Operations]
    ToolSelect --> Planning[Planning]
    
    PythonExec --> Result[Result]
    WebBrowsing --> Result
    GoogleSearch --> Result
    FileOps --> Result
    Planning --> Result
    
    Result --> Agent
    
    %% Styling
    classDef default fill:#f0f0ff,stroke:#333,stroke-width:1px
    classDef decision fill:#f5f5ff,stroke:#333,stroke-width:1px,shape:diamond
    
    class ToolSelect decision
```

## Main Components

### 1. Agent System
- **BaseAgent**: The base class for all agents.
- **ToolAgent**: An agent with tool invocation capabilities.
- **AutoPlanAgent**: An agent capable of automatic planning, execution, and self-repair with COAT integration.

### 2. Flow System
- **BaseFlow**: The base class for flows.
- **PlanningFlow**: Manages planning and execution flows.

### 3. Tool System
- **PlanningTool**: For planning and managing tasks.
- **PythonExecuteTool**: For executing Python code.
- **PythonProjectExecuteTool**: For executing Python code in a project environment.
- **FileTool**: For file operations.
- **DockerExecuteTool**: For executing Docker commands.
- **SystemTool**: For system operations.

### 4. Learning System
- **GraphRAGManager**: For learning and retrieving error and code patterns.
- **ModularCodeManager**: For managing reusable code modules.

### 5. LLLM Technologies
- **LocalModelManager**: Manages local LLM models with MPS acceleration support.
- **ROMEModelEditor**: Implements Rank-One Model Editing for direct knowledge modification in LLMs.
- **COATReasoner**: Implements Chain-of-Action-Thought methodology for self-reflection and error correction.
- **RGCNProcessor**: Implements Relational Graph Convolutional Networks for knowledge graph processing.

### 6. Database
- **TaskDatabase**: An SQLite-based task and plan manager.

### 7. Environment Management
- **ProjectEnvironment**: Manages virtual environments on a per-project basis.

## Workflow

1. **Goal Input**: The user inputs the goal to be achieved.
2. **Plan Generation**: The goal is broken down into smaller tasks.
3. **Code Generation**: Python code is automatically generated for each task.
4. **Environment Setup**: An isolated environment is prepared for task execution.
5. **Task Execution**: Tasks are executed sequentially with dependency management.
6. **Error Handling**: Failed tasks are automatically corrected.
7. **Learning**: Successful patterns are recorded for future tasks.
8. **Result Reporting**: A summary of the execution results is generated and returned.

## Learning System

SynthepseAI Agent incorporates two learning mechanisms:

### GraphRAG Learning System
- **Error Pattern Learning**: Records encountered errors and successful fixes.
- **Task Template Learning**: Accumulates successful code patterns for each task type.
- **Contextual Retrieval**: Uses similar task resolutions to enhance prompt performance.

### Module Reuse System
- **Module Extraction**: Extracts reusable code from successful tasks.
- **Dependency Management**: Maintains dependencies between modules.
- **Contextual Application**: Automatically incorporates relevant modules into new tasks.

## Extending the System

### Adding New Tools

1. Create a new tool class in the `core/tools/` directory.
2. Inherit from `BaseTool` and implement the necessary methods.
3. Register the new tool with `AutoPlanAgent`.

```python
# Example of creating a new tool
class NewTool(BaseTool):
    def __init__(self):
        super().__init__("new_tool", "Description of the new tool")
        self.parameters = {...}
    
    def execute(self, **kwargs) -> ToolResult:
        # Implementation...
        return ToolResult(...)

# Registering the tool
agent.available_tools.add_tool(new_tool)
```

### Extending the Learning System

1. Add new search and storage methods to `GraphRAGManager`.
2. Extend the Weaviate schema to store new data types.

## Troubleshooting

### Common Issues and Solutions

#### OpenAI API Connection Error
```
Error: OpenAI API connection failed...
```
*Solution*: Verify that the API key is correctly set. Also, check your network connection and the status of the OpenAI API.

#### ModuleNotFoundError
```
ModuleNotFoundError: No module named 'some_module'
```
*Solution*: Manually install the required package or use the `--debug` flag for more details.

#### SQLite Database Error
```
sqlite3.OperationalError: no such table...
```
*Solution*: Ensure that the database file exists. If necessary, delete it and create a new database.

#### Weaviate Connection Error
```
Error connecting to Weaviate...
```
*Solution*: Verify that the Weaviate container is running by executing `docker-compose -f weaviate-docker-compose.yml ps` to check its status.

## License

MIT License

## Contribution Guidelines

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/amazing-feature`).
3. Commit your changes (`git commit -m 'Add amazing feature'`).
4. Push the branch (`git push origin feature/amazing-feature`).
5. Create a Pull Request.

## Developer Information

### Code Style
- Adheres to PEP 8 coding style.
- Docstrings are required for all classes and public methods.
- Code formatting follows the Black style.

### Testing
```bash
# Run tests
python -m unittest discover tests
```

### Documentation Generation
```bash
# Generate API documentation
sphinx-build -b html docs/source docs/build
```

---

**Note**: This system is under development and may behave unexpectedly. Please create backups of any critical data before processing.

**Version**: 0.1.0
