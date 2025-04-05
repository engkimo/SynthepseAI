# main.py (プロジェクト環境統合版)
import os
import argparse
import json

from core.llm import LLM
from core.task_database import TaskDatabase
from core.tools.planning_tool import PlanningTool
from core.tools.python_project_execute import PythonProjectExecuteTool
from core.tools.file_tool import FileTool
from core.tools.docker_execute import DockerExecuteTool
from core.tools.system_tool import SystemTool
from core.auto_plan_agent import AutoPlanAgent
from core.planning_flow import PlanningFlow
from core.enhanced_persistent_thinking_ai import EnhancedPersistentThinkingAI
from core.lllm_multi_agent_flow import LLLMMultiAgentFlow
from core.multi_agent.multi_agent_system import MultiAgentSystem
from core.rome_model_editor import ROMEModelEditor
from core.coat_reasoner import COATReasoner
from core.rgcn_processor import RGCNProcessor

def main():
    parser = argparse.ArgumentParser(description='Run the AI Agent system')
    parser.add_argument('--goal', type=str, help='The goal to accomplish')
    parser.add_argument('--workspace', type=str, default='./workspace', help='The workspace directory for file operations')
    parser.add_argument('--config', type=str, default='./config.json', help='Configuration file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--mock', action='store_true', help='Run in mock mode without API calls')
    
    args = parser.parse_args()
    
    # 設定ファイルのロード
    config = {}
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    openai_api_key = config.get('openai_api_key')
    mock_mode = args.mock
    
    if not openai_api_key and not mock_mode:
        print("警告: OpenAI APIキーが設定されていません。モックモードで実行します。")
        mock_mode = True
    
    # Initialize components
    llm = LLM(
        api_key=openai_api_key,
        model=config.get('model', 'gpt-4-turbo'),
        temperature=config.get('temperature', 0.7),
        mock_mode=mock_mode
    )
    
    # ワークスペースディレクトリを作成
    os.makedirs(args.workspace, exist_ok=True)
    
    persistent_thinking_dir = os.path.join(args.workspace, 'persistent_thinking')
    os.makedirs(persistent_thinking_dir, exist_ok=True)
    persistent_thinking = EnhancedPersistentThinkingAI(
        model_name=config.get('local_model_name', 'microsoft/phi-2'),
        workspace_dir=persistent_thinking_dir,
        knowledge_db_path=os.path.join(persistent_thinking_dir, 'knowledge_db.json'),
        log_path=os.path.join(persistent_thinking_dir, 'thinking_log.jsonl'),
        device=config.get('device', 'cpu'),
        use_compatibility_mode=True,  # 互換モードを有効化
        tavily_api_key=config.get('tavily_api_key'),
        firecrawl_api_key=config.get('firecrawl_api_key')
    )
    
    # デバッグモードが有効な場合のログ設定
    if args.debug:
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(args.workspace, 'debug.log')),
                logging.StreamHandler()
            ]
        )
    
    # タスクデータベースの初期化（SQLiteに変更）
    db_path = os.path.join(args.workspace, 'tasks.db')
    task_db = TaskDatabase(db_path)
    
    # ツールの初期化
    planning_tool = PlanningTool(llm, task_db)
    project_executor = PythonProjectExecuteTool(args.workspace, task_db)
    file_tool = FileTool(args.workspace)
    docker_tool = DockerExecuteTool(args.workspace)
    system_tool = SystemTool()
    
    # エージェントの初期化
    agent = AutoPlanAgent(
        "AutoPlanAgent", 
        "An agent that automatically plans and executes tasks", 
        llm, 
        task_db,
        args.workspace,
        graph_rag=None,
        modular_code_manager=None,
        persistent_thinking=persistent_thinking  # 持続思考AIを渡す
    )
    agent.set_planner(planning_tool)
    agent.set_project_executor(project_executor)
    agent.available_tools.add_tool(file_tool)
    agent.available_tools.add_tool(docker_tool)
    agent.available_tools.add_tool(system_tool)
    
    planning_flow = PlanningFlow(llm, task_db)
    planning_flow.add_agent("auto_plan", agent)
    planning_flow.set_planning_tool(planning_tool)
    
    lllm_flow = LLLMMultiAgentFlow(
        llm=llm,
        task_db=task_db,
        workspace_dir=args.workspace,
        config={
            "device": config.get("device", "cpu"),
            "tavily_api_key": config.get("tavily_api_key"),
            "firecrawl_api_key": config.get("firecrawl_api_key"),
            "rgcn_hidden_dim": config.get("rgcn_hidden_dim", 64),
            "use_compatibility_mode": config.get("use_compatibility_mode", True),
            "mock_mode": mock_mode
        }
    )
    
    # ゴールが指定されている場合はフローを実行
    if args.goal:
        print(f"Starting execution with goal: '{args.goal}'")
        print(f"Working directory: {args.workspace}")
        
        use_lllm = config.get("use_lllm_flow", True)
        
        if use_lllm:
            print("Using LLLM Multi-Agent Flow")
            result = lllm_flow.execute(args.goal)
        else:
            print("Using Traditional Planning Flow")
            result = planning_flow.execute(args.goal)
            
        print(result)
    else:
        print("Please provide a goal using the --goal argument")
        print("Example: python main.py --goal 'Analyze the data in data.csv and create a visualization'")

if __name__ == "__main__":
    main()
