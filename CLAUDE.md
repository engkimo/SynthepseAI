# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up DGL compatibility for Python 3.12
source set_env.sh  # Or: export DGL_COMPATIBILITY_MODE=1

# Configure API keys
cp config.json.example config.json
# Edit config.json to add API keys (OpenAI, OpenRouter, Tavily, Firecrawl)

# Start Weaviate (optional, for GraphRAG features)
docker-compose up -d
```

### Running the System
```bash
# Execute with a goal
python main.py --goal "Create a CSV file and analyze the data"

# With custom workspace
python main.py --goal "Task description" --workspace ./custom_workspace

# Debug mode
python main.py --goal "Task" --debug

# Run with Weaviate for learning features
python main.py --goal "Task" --weaviate-url "http://localhost:8080"
```

### Testing
```bash
# Run specific test examples
python examples/test_integration.py
python examples/test_openrouter.py
python examples/test_persistent_thinking.py
python examples/test_multi_agent.py
python examples/enhanced_thinking_example.py
```

## High-Level Architecture

### System Overview
SynthepseAI is an autonomous AI agent system implementing the LLLM (Larger LLM) concept. It combines multiple AI technologies to create a self-correcting, learning system that can plan and execute complex tasks.

### Core Architecture Flow
```
User Goal → PlanningFlow → AutoPlanAgent → Task Decomposition
                ↓                ↓              ↓
          TaskDatabase    Tools/Execution   Learning Systems
                ↓                ↓              ↓
          SQLite Storage  Isolated Envs   GraphRAG/Knowledge
```

### Key Components Interaction

1. **Agent Hierarchy**
   - `BaseAgent` → `ToolAgent` → `AutoPlanAgent`
   - Agents communicate through `BaseFlow` and `PlanningFlow`
   - Each agent has access to tools via `ToolCollection`

2. **Execution Flow**
   - User provides goal → `PlanningFlow` creates plan
   - `AutoPlanAgent` decomposes into tasks
   - Each task executed in isolated `ProjectEnvironment`
   - Results stored in `TaskDatabase`
   - Learning systems capture patterns

3. **Knowledge Management**
   - `EnhancedPersistentThinkingAI` manages continuous learning
   - `GraphRAGManager` stores error patterns and solutions
   - Knowledge graph in `knowledge_graph.json`
   - Thinking logs in `workspace/persistent_thinking/thinking_log.jsonl`

4. **Tool Integration**
   - Tools inherit from `BaseTool`
   - Registered in `ToolCollection`
   - Key tools: `PythonProjectExecuteTool`, `WebCrawlingTool`, `FileTool`
   - Each tool returns `ToolResult` with success/error states

### Critical Design Patterns

1. **Isolated Execution**
   - Each project gets unique ID and virtual environment
   - Dependencies managed per-project in `workspace/project_*/`
   - Prevents cross-project contamination

2. **Self-Correction Loop**
   - Execute task → Detect error → Query GraphRAG for solutions
   - Apply learned fixes → Retry → Update knowledge base
   - Maximum retry attempts configurable

3. **API Fallback Chain**
   - Primary API → Legacy API → Direct calls → Alternative service → Mock mode
   - Ensures continuous operation without external dependencies

4. **Template-Based Code Generation**
   - `script_templates.py` provides base templates
   - Templates include error handling and knowledge integration
   - `ScriptLinter` auto-fixes common issues

### Configuration Architecture

**config.json Structure**:
- `llm_provider`: "openai" or "openrouter"
- `model`: Model selection (e.g., "gpt-4o")
- `specialized_agents`: Multi-agent configurations
- `error_handling`: Retry and correction settings
- API keys for various services

**Environment Management**:
- `.env` file for sensitive keys
- `DGL_COMPATIBILITY_MODE=1` for Python 3.12
- Docker for Weaviate vector database

### Knowledge Systems Integration

1. **ROME (Knowledge Editing)**
   - Direct modification of model's internal knowledge
   - Implemented in `rome_model_editor.py`

2. **COAT (Chain-of-Action-Thought)**
   - Self-reflective reasoning chains
   - Improves decision-making and error correction

3. **R-GCN (Graph Neural Networks)**
   - Processes knowledge graphs for pattern recognition
   - Falls back to NetworkX if DGL unavailable

### Development Patterns

**Adding New Capabilities**:
- New tools: Inherit `BaseTool`, implement `execute()`, register with agent
- New agents: Inherit `BaseAgent`, override `step()`, add to flow
- New learning: Extend `GraphRAGManager` or `EnhancedPersistentThinkingAI`

**Error Handling Strategy**:
- All tools return `ToolResult` with success flag
- Errors logged with context for learning
- Automatic retry with learned corrections
- Fallback to mock mode if APIs unavailable

**Testing Approach**:
- Integration tests in `examples/test_*.py`
- Mock mode enables testing without APIs
- Each component testable in isolation