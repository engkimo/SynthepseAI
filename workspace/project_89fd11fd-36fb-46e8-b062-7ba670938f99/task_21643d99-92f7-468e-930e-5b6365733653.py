from typing import Dict, List, Any, Optional, Union, Tuple
import os
import json
import time
import re
import datetime
import traceback

KNOWLEDGE_DB_PATH = "./workspace/persistent_thinking/knowledge_db.json"
THINKING_LOG_PATH = "./workspace/persistent_thinking/thinking_log.jsonl"

task_info = {
    "task_id": "21643d99-92f7-468e-930e-5b6365733653",
    "description": "Import necessary Python libraries for data analysis and visualization.",
    "plan_id": "89fd11fd-36fb-46e8-b062-7ba670938f99",
}

task_description = ""
insights = []
hypotheses = []
conclusions = []

def get_related_knowledge(keywords, limit=5):
    """
    Get knowledge related to keywords
    
    Args:
        keywords: List of search keywords
        limit: Maximum number of results to return
        
    Returns:
        List of related knowledge
    """
    try:
        knowledge_db = load_knowledge_db()
        related = []
        
        for subject, data in knowledge_db.items():
            for keyword in keywords:
                if keyword.lower() in subject.lower() or (
                    data.get("fact") and keyword.lower() in data.get("fact", "").lower()
                ):
                    related.append({
                        "subject": subject,
                        "fact": data.get("fact"),
                        "confidence": data.get("confidence", 0),
                        "last_updated": data.get("last_updated"),
                        "source": data.get("source"),
                    })
                    break
                    
        related.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return related[:limit]
    except Exception as e:
        print(f"Error getting related knowledge: {str(e)}")
        return []

def load_knowledge_db():
    """Load knowledge database"""
    try:
        if os.path.exists(KNOWLEDGE_DB_PATH):
            with open(KNOWLEDGE_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading knowledge database: {str(e)}")
        return {}

def save_knowledge_db(knowledge_db):
    """Save knowledge database"""
    try:
        os.makedirs(os.path.dirname(KNOWLEDGE_DB_PATH), exist_ok=True)
        with open(KNOWLEDGE_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(knowledge_db, fp=f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving knowledge database: {str(e)}")
        return False

def log_thought(thought_type, content):
    """Record thought log"""
    try:
        os.makedirs(os.path.dirname(THINKING_LOG_PATH), exist_ok=True)
        with open(THINKING_LOG_PATH, 'a', encoding='utf-8') as f:
            log_entry = {
                "timestamp": time.time(),
                "type": thought_type,
                "content": content
            }
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"Error recording thought log: {str(e)}")
        return False

def get_task_related_knowledge(task_description):
    """
    Extract keywords from task description and get related knowledge
    
    Args:
        task_description: Task description
        
    Returns:
        Dictionary of related knowledge
    """
    try:
        keywords = task_description.lower().split()
        keywords = [word for word in keywords if len(word) > 3]  # Exclude short words
        
        related_knowledge = get_related_knowledge(keywords)
        
        insights = get_task_insights(task_description)
        
        return {
            "related_knowledge": related_knowledge,
            "insights": insights
        }
    except Exception as e:
        print(f"Error getting task related knowledge: {str(e)}")
        return {"related_knowledge": [], "insights": []}

def get_task_insights(task_description):
    """
    Get insights related to task from thought log
    
    Args:
        task_description: Task description
        
    Returns:
        List of related insights
    """
    try:
        insights = []
        if os.path.exists(THINKING_LOG_PATH):
            with open(THINKING_LOG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("type") == "task_insight":
                            if task_description.lower() in entry.get("content", {}).get("task", "").lower():
                                insights.append({
                                    "insight": entry.get("content", {}).get("insight", ""),
                                    "confidence": entry.get("content", {}).get("confidence", 0)
                                })
                    except:
                        continue
        return insights
    except Exception as e:
        print(f"Error getting task insights: {str(e)}")
        return []

def update_knowledge(subject, fact, confidence=0.8, source=None):
    """Update knowledge database"""
    try:
        if not subject or not fact:
            return False
            
        knowledge_db = load_knowledge_db()
        
        original_fact = None
        if subject in knowledge_db:
            original_fact = knowledge_db[subject].get("fact")
        else:
            knowledge_db[subject] = {}
            
        knowledge_db[subject]["fact"] = fact
        knowledge_db[subject]["confidence"] = confidence
        knowledge_db[subject]["last_updated"] = time.time()
        
        if source:
            knowledge_db[subject]["source"] = source
        else:
            knowledge_db[subject]["source"] = "thinking_process"
        
        save_success = save_knowledge_db(knowledge_db)
        
        log_thought(
            "knowledge_update",
            {
                "subject": subject,
                "original_fact": original_fact,
                "new_fact": fact,
                "confidence": confidence,
                "source": source,
                "success": save_success,
            }
        )
        
        return save_success
    except Exception as e:
        print(f"Error updating knowledge: {str(e)}")
        return False

def add_insight(insight_text, confidence=0.7):
    """Add insight"""
    global insights
    try:
        insights.append({"text": insight_text, "confidence": confidence})
        log_thought("task_insight", {"task": task_description, "insight": insight_text, "confidence": confidence})
        return True
    except Exception as e:
        print(f"Error adding insight: {str(e)}")
        return False

def add_hypothesis(hypothesis_text, confidence=0.6):
    """Add hypothesis"""
    global hypotheses
    try:
        hypotheses.append({"text": hypothesis_text, "confidence": confidence, "verified": False})
        log_thought("task_hypothesis", {"task": task_description, "hypothesis": hypothesis_text, "confidence": confidence})
        return True
    except Exception as e:
        print(f"Error adding hypothesis: {str(e)}")
        return False

def verify_hypothesis(hypothesis_index, is_valid, evidence=None):
    """Verify hypothesis"""
    global hypotheses
    try:
        if hypothesis_index < 0 or hypothesis_index >= len(hypotheses):
            return False
            
        hypotheses[hypothesis_index]["verified"] = True
        hypotheses[hypothesis_index]["is_valid"] = is_valid
        
        if evidence:
            hypotheses[hypothesis_index]["evidence"] = evidence
            
        log_thought(
            "hypothesis_verification",
            {
                "task": task_description,
                "hypothesis": hypotheses[hypothesis_index]["text"],
                "is_valid": is_valid,
                "evidence": evidence
            }
        )
        
        return True
    except Exception as e:
        print(f"Error verifying hypothesis: {str(e)}")
        return False

def verify_hypothesis_with_simulation(hypothesis_text, simulation_code):
    """Verify hypothesis using simulation"""
    try:
        print(f"Verifying hypothesis '{hypothesis_text}' with simulation...")
        
        hypothesis_index = len(hypotheses)
        add_hypothesis(hypothesis_text)
        
        simulation_result = None
        simulation_error = None
        
        try:
            simulation_locals = {}
            
            exec(simulation_code, {}, simulation_locals)
            
            simulation_result = simulation_locals.get("result")
        except Exception as e:
            simulation_error = str(e)
            print(f"Simulation error: {simulation_error}")
        
        is_valid = simulation_error is None and simulation_result is not None
        
        evidence = {
            "simulation_result": simulation_result,
            "simulation_error": simulation_error,
            "simulation_code": simulation_code
        }
        
        verify_hypothesis(hypothesis_index, is_valid, evidence)
        
        return {
            "hypothesis": hypothesis_text,
            "is_valid": is_valid,
            "evidence": evidence
        }
    except Exception as e:
        print(f"Error in simulation verification: {str(e)}")
        return {
            "hypothesis": hypothesis_text,
            "is_valid": False,
            "error": str(e)
        }

def add_conclusion(conclusion_text, confidence=0.8, supporting_insights=None):
    """Add conclusion"""
    global conclusions
    try:
        conclusion = {
            "text": conclusion_text,
            "confidence": confidence,
            "timestamp": time.time()
        }
        
        if supporting_insights:
            conclusion["supporting_insights"] = supporting_insights
            
        conclusions.append(conclusion)
        
        log_thought(
            "task_conclusion",
            {
                "task": task_description,
                "conclusion": conclusion_text,
                "confidence": confidence,
                "supporting_insights": supporting_insights
            }
        )
        
        return True
    except Exception as e:
        print(f"Error adding conclusion: {str(e)}")
        return False

def request_multi_agent_discussion(topic):
    """Request multi-agent discussion"""
    try:
        log_thought(
            "multi_agent_discussion_request",
            {
                "topic": topic,
                "timestamp": time.time()
            }
        )
        
        return {"topic": topic, "requested": True, "timestamp": time.time()}
    except Exception as e:
        print(f"Error requesting multi-agent discussion: {str(e)}")
        return {}

def main():
    global task_description, insights, hypotheses, conclusions
    
    try:
        task_info = globals().get("task_info", {})
        task_description = task_info.get("description", "Unknown task")
        task_start_time = time.time()
        
        log_thought(
            "task_execution_start",
            {
                "task": task_description,
                "timestamp_readable": datetime.datetime.now().isoformat(),
            }
        )
        
        keywords = [word for word in task_description.lower().split() if len(word) > 3]
        
        related_knowledge = []
        try:
            knowledge_db = load_knowledge_db()
            for subject, data in knowledge_db.items():
                for keyword in keywords:
                    if keyword.lower() in subject.lower() or (
                        data.get("fact") and keyword.lower() in data.get("fact", "").lower()
                    ):
                        related_knowledge.append({
                            "subject": subject,
                            "fact": data.get("fact"),
                            "confidence": data.get("confidence", 0),
                            "last_updated": data.get("last_updated"),
                            "source": data.get("source"),
                        })
                        break
                        
            error_patterns = []
            thinking_log_path = THINKING_LOG_PATH
            if os.path.exists(thinking_log_path):
                with open(thinking_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("type") == "task_execution_error":
                                content = entry.get("content", {})
                                error_patterns.append({
                                    "error_type": content.get("error_type", "unknown"),
                                    "error_message": content.get("error_message", ""),
                                })
                        except:
                            continue
                            
            if error_patterns:
                add_insight(f"Analyzed {len(error_patterns)} past error patterns to avoid similar errors", confidence=0.8)
                for pattern in error_patterns[-3:]:  # Consider the latest 3 error patterns
                    add_hypothesis(f"Need appropriate measures to avoid error '{pattern['error_type']}'", confidence=0.7)
        except Exception as e:
            print(f"Error getting related knowledge: {str(e)}")
            
        if related_knowledge:
            print(f"Found {len(related_knowledge)} existing knowledge items related to task '{task_description}':")
            for i, knowledge in enumerate(related_knowledge):
                print(f"  {i+1}. {knowledge['subject']}: {knowledge['fact']} (confidence: {knowledge['confidence']:.2f})")
                
            if len(related_knowledge) >= 2:
                hypothesis = f"Task '{task_description}' may be related to {related_knowledge[0]['subject']} and {related_knowledge[1]['subject']}"
                add_hypothesis(hypothesis, confidence=0.6)
                
                for i in range(min(len(related_knowledge), 3)):
                    for j in range(i + 1, min(len(related_knowledge), 4)):
                        if i != j:
                            insight = f"Combining {related_knowledge[i]['subject']} and {related_knowledge[j]['subject']} might provide a new perspective"
                            add_insight(insight, confidence=0.65)
        else:
            print(f"No existing knowledge found related to task '{task_description}'.")
            add_insight("No existing knowledge related to this task, need to acquire new knowledge")
            
            discussion_request = request_multi_agent_discussion(f"Basic knowledge and hypotheses about '{task_description}'")
            if discussion_request:
                add_insight(f"Requested multi-agent discussion: {task_description}", confidence=0.8)
        
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns
        from sklearn import datasets
        
        add_insight("Pandas is essential for data manipulation and analysis", confidence=0.9)
        add_insight("NumPy provides numerical computing capabilities", confidence=0.9)
        add_insight("Matplotlib and Seaborn are powerful visualization libraries", confidence=0.85)
        add_insight("Scikit-learn provides machine learning algorithms and datasets", confidence=0.8)
        
        update_knowledge(
            "Pandas",
            "A powerful data analysis and manipulation library for Python",
            confidence=0.95,
            source="library_import"
        )
        
        update_knowledge(
            "NumPy",
            "A fundamental package for scientific computing with Python",
            confidence=0.95,
            source="library_import"
        )
        
        update_knowledge(
            "Matplotlib",
            "A comprehensive library for creating static, animated, and interactive visualizations in Python",
            confidence=0.9,
            source="library_import"
        )
        
        update_knowledge(
            "Seaborn",
            "A statistical data visualization library based on matplotlib",
            confidence=0.85,
            source="library_import"
        )
        
        update_knowledge(
            "Scikit-learn",
            "A machine learning library that features various classification, regression and clustering algorithms",
            confidence=0.9,
            source="library_import"
        )
        
        add_conclusion(
            "Successfully imported necessary Python libraries for data analysis and visualization",
            confidence=0.95,
            supporting_insights=[
                "Pandas and NumPy provide core data processing capabilities",
                "Matplotlib and Seaborn enable comprehensive data visualization",
                "Scikit-learn provides access to datasets and machine learning algorithms"
            ]
        )
        
        result = "Successfully imported data analysis and visualization libraries"
        
        log_thought(
            "task_execution_complete",
            {
                "task": task_description,
                "execution_time": time.time() - task_start_time,
                "insights_count": len(insights),
                "hypotheses_count": len(hypotheses),
                "conclusions_count": len(conclusions),
            }
        )
        
        return result
        
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else str(e)
        error_msg = f"Error: Required module '{missing_module}' is not installed."
        print(error_msg)
        print(f"Install it with: pip install {missing_module}")
        
        try:
            log_thought(
                "task_execution_error",
                {
                    "task": task_description,
                    "error_type": "ImportError",
                    "error_message": error_msg,
                }
            )
        except:
            pass
            
        return error_msg
        
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        print(error_details)
        
        try:
            log_thought(
                "task_execution_error",
                {
                    "task": task_description,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": error_details,
                }
            )
            
            update_knowledge(
                f"Error pattern: {type(e).__name__}",
                f"Occurred during task execution: {str(e)}",
                confidence=0.7,
            )
        except:
            pass
            
        return error_msg

if __name__ == "__main__":
    result = main()
    print(f"Task result: {result}")
