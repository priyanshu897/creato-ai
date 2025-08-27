import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple, Any
from models import WorkflowThread, AgentResult, AgentMessage
import os
from pathlib import Path
import json

class WorkflowManager:
    def __init__(self):
        self.workflows: Dict[str, WorkflowThread] = {}
        self.workflow_status: Dict[str, str] = {}
        self.agent_results: Dict[str, List[AgentResult]] = {}
        self.workflow_messages: Dict[str, List[AgentMessage]] = {}
        # Simple checkpointing directory (can be swapped with LangGraph checkpointer)
        self.checkpoint_dir = Path(".wf_checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        # Subscribers for realtime notifications per workflow
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}
        
    def add_workflow(self, workflow: WorkflowThread):
        """Add a new workflow to the manager"""
        self.workflows[workflow.id] = workflow
        self.workflow_status[workflow.id] = workflow.status
        self.agent_results[workflow.id] = []
        self.workflow_messages[workflow.id] = []
        
        print(f"Added workflow {workflow.id}: {workflow.user_input}")
        self._save_checkpoint(workflow.id)
        self._notify_subscribers(workflow.id, {"type": "workflow_added", "workflow_id": workflow.id})
        
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowThread]:
        """Get a specific workflow by ID"""
        return self.workflows.get(workflow_id)
        
    def get_all_workflows(self) -> List[WorkflowThread]:
        """Get all workflows"""
        return list(self.workflows.values())
        
    def update_workflow_status(self, workflow_id: str, status: str):
        """Update the status of a workflow"""
        if workflow_id in self.workflows:
            self.workflows[workflow_id].status = status
            self.workflow_status[workflow_id] = status
            print(f"Workflow {workflow_id} status updated to: {status}")
            self._save_checkpoint(workflow_id)
            self._notify_subscribers(workflow_id, {"type": "status", "workflow_id": workflow_id, "status": status})
            
    def add_agent_result(self, workflow_id: str, agent_name: str, result: str):
        """Add an agent result to a workflow"""
        if workflow_id in self.agent_results:
            agent_result = AgentResult(
                agent_name=agent_name,
                result=result,
                timestamp=datetime.utcnow()
            )
            self.agent_results[workflow_id].append(agent_result)
            
            # Also add to workflow messages
            message = AgentMessage(
                sender=agent_name,
                content=result,
                timestamp=datetime.utcnow(),
                message_type="agent_result"
            )
            self.add_message(workflow_id, result, agent_name)
            
            print(f"Added result from {agent_name} to workflow {workflow_id}")
            self._save_checkpoint(workflow_id)
            self._notify_subscribers(workflow_id, {"type": "agent_result", "workflow_id": workflow_id, "agent": agent_name, "result": result})
            
    def add_message(self, workflow_id: str, content: str, sender: str):
        """Add a message to a workflow"""
        if workflow_id in self.workflow_messages:
            message = AgentMessage(
                sender=sender,
                content=content,
                timestamp=datetime.utcnow(),
                message_type="chat" if sender == "user" else "agent_result"
            )
            self.workflow_messages[workflow_id].append(message)
            self._save_checkpoint(workflow_id)
            self._notify_subscribers(workflow_id, {"type": "message", "workflow_id": workflow_id, "message": message.dict()})
            
    def get_workflow_messages(self, workflow_id: str) -> List[AgentMessage]:
        """Get all messages for a workflow"""
        return self.workflow_messages.get(workflow_id, [])
        
    def get_workflow_agent_results(self, workflow_id: str) -> List[AgentResult]:
        """Get all agent results for a workflow"""
        return self.agent_results.get(workflow_id, [])
        
    def get_workflow_summary(self, workflow_id: str) -> Dict:
        """Get a summary of a workflow including status, agents, and recent messages"""
        if workflow_id not in self.workflows:
            return None
            
        workflow = self.workflows[workflow_id]
        messages = self.get_workflow_messages(workflow_id)
        agent_results = self.get_workflow_agent_results(workflow_id)
        
        return {
            "id": workflow.id,
            "user_input": workflow.user_input,
            "status": workflow.status,
            "created_at": workflow.created_at.isoformat(),
            "agent_count": len(agent_results),
            "message_count": len(messages),
            "recent_messages": messages[-5:] if messages else [],  # Last 5 messages
            "agents_used": [result.agent_name for result in agent_results]
        }
        
    def delete_workflow(self, workflow_id: str):
        """Delete a workflow and all its associated data"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            
        if workflow_id in self.workflow_status:
            del self.workflow_status[workflow_id]
            
        if workflow_id in self.agent_results:
            del self.agent_results[workflow_id]
            
        if workflow_id in self.workflow_messages:
            del self.workflow_messages[workflow_id]
            
        print(f"Deleted workflow {workflow_id}")
        
    def get_workflow_stats(self) -> Dict:
        """Get overall statistics about all workflows"""
        total_workflows = len(self.workflows)
        completed_workflows = sum(1 for status in self.workflow_status.values() if status == "completed")
        processing_workflows = sum(1 for status in self.workflow_status.values() if status == "processing")
        error_workflows = sum(1 for status in self.workflow_status.values() if "error" in status)
        
        total_agents_run = sum(len(results) for results in self.agent_results.values())
        total_messages = sum(len(messages) for messages in self.workflow_messages.values())
        
        return {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "processing_workflows": processing_workflows,
            "error_workflows": error_workflows,
            "total_agents_run": total_agents_run,
            "total_messages": total_messages,
            "success_rate": (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0
        }
        
    def cleanup_old_workflows(self, days_old: int = 30):
        """Clean up workflows older than specified days"""
        cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
        
        workflows_to_delete = []
        for workflow_id, workflow in self.workflows.items():
            if workflow.created_at < cutoff_date:
                workflows_to_delete.append(workflow_id)
                
        for workflow_id in workflows_to_delete:
            self.delete_workflow(workflow_id)
            
        print(f"Cleaned up {len(workflows_to_delete)} old workflows")
        
    def export_workflow_data(self, workflow_id: str) -> str:
        """Export workflow data as JSON string"""
        if workflow_id not in self.workflows:
            return None
            
        workflow = self.workflows[workflow_id]
        messages = self.get_workflow_messages(workflow_id)
        agent_results = self.get_workflow_agent_results(workflow_id)
        
        export_data = {
            "workflow": {
                "id": workflow.id,
                "user_input": workflow.user_input,
                "status": workflow.status,
                "created_at": workflow.created_at.isoformat()
            },
            "messages": [msg.dict() for msg in messages],
            "agent_results": [result.dict() for result in agent_results]
        }
        
        return json.dumps(export_data, indent=2, default=str)

    # --- Checkpointing helpers ---
    def _checkpoint_path(self, workflow_id: str) -> Path:
        return self.checkpoint_dir / f"{workflow_id}.json"

    def _save_checkpoint(self, workflow_id: str) -> None:
        """Persist workflow thread, messages, and results to disk."""
        try:
            data = {
                "workflow": self.workflows.get(workflow_id).dict() if workflow_id in self.workflows else None,
                "status": self.workflow_status.get(workflow_id),
                "messages": [m.dict() for m in self.workflow_messages.get(workflow_id, [])],
                "agent_results": [r.dict() for r in self.agent_results.get(workflow_id, [])],
                "saved_at": datetime.utcnow().isoformat(),
            }
            with self._checkpoint_path(workflow_id).open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"[Checkpoint] save failed for {workflow_id}: {e}")

    def load_checkpoint(self, workflow_id: str) -> Optional[Dict]:
        """Load persisted state if available and hydrate in-memory stores."""
        path = self._checkpoint_path(workflow_id)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            wf = data.get("workflow")
            if wf:
                self.workflows[workflow_id] = WorkflowThread(**wf)
                self.workflow_status[workflow_id] = data.get("status", wf.get("status", "processing"))
            self.workflow_messages[workflow_id] = [AgentMessage(**m) for m in data.get("messages", [])]
            self.agent_results[workflow_id] = [AgentResult(**r) for r in data.get("agent_results", [])]
            print(f"[Checkpoint] loaded {workflow_id}")
            return data
        except Exception as e:
            print(f"[Checkpoint] load failed for {workflow_id}: {e}")
            return None

    def load_all_checkpoints(self) -> None:
        """Load all persisted workflows on startup."""
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            workflow_id = checkpoint_file.stem
            self.load_checkpoint(workflow_id)

    # --- Simple execution scaffolding (can be replaced by LangGraph integration) ---
    def validate_user_input(self, workflow_id: str, user_input: str) -> Tuple[bool, str]:
        if workflow_id not in self.workflows:
            return False, "Workflow not found"
        current_messages = self.get_workflow_messages(workflow_id)
        # Naive detection based on last status stored
        current_step = self.workflow_status.get(workflow_id, "start")
        if current_step == "waiting_for_selection":
            if user_input.isdigit():
                n = int(user_input)
                if 1 <= n <= 5:
                    return True, ""
                return False, "Please select a number between 1 and 5"
            if user_input.lower() == "refine":
                return True, ""
            return False, "Please select an idea (1-5) or type 'refine'"
        # Default valid
        return True, ""

    def subscribe_to_updates(self, workflow_id: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.setdefault(workflow_id, []).append(callback)

    def _notify_subscribers(self, workflow_id: str, data: Dict[str, Any]) -> None:
        for cb in self._subscribers.get(workflow_id, []):
            try:
                cb(data)
            except Exception as e:
                print(f"Error in subscriber callback: {e}")

    def execute_workflow_step(self, workflow_id: str, user_input: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if workflow_id not in self.workflows:
            return None
        checkpoint = self.load_checkpoint(workflow_id) or {}
        state = checkpoint.get("state", {"current_step": "start"})
        if user_input:
            state["user_input"] = user_input
            self.add_message(workflow_id, user_input, "user")
        try:
            result = self._run_workflow_step(workflow_id, state)
            # Save state back into checkpoint bundle
            data = self.load_checkpoint(workflow_id) or {}
            data["state"] = state
            with self._checkpoint_path(workflow_id).open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self._notify_subscribers(workflow_id, {"type": "step", "workflow_id": workflow_id, "state": state})
            return result
        except Exception as e:
            self.update_workflow_status(workflow_id, f"error: {e}")
            return {"error": str(e)}

    def _run_workflow_step(self, workflow_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        current_step = state.get("current_step", "start")
        if current_step == "start":
            # Mock ideation (replace with LangGraph call)
            ideas = [{"title": f"Idea {i+1}", "summary": ""} for i in range(5)]
            state["content_ideas"] = ideas
            state["current_step"] = "waiting_for_selection"
            self.update_workflow_status(workflow_id, "waiting_for_selection")
            ideas_text = "\n".join([f"{i+1}. {it['title']}" for i, it in enumerate(ideas)])
            self.add_agent_result(workflow_id, "ideation_agent", f"Generated ideas:\n{ideas_text}")
            return {"required_input": {"kind": "selection", "options": [{"index": i+1, "title": it["title"]} for i, it in enumerate(ideas)]}}
        if current_step == "waiting_for_selection":
            ui = state.get("user_input", "").strip().lower()
            if ui.isdigit():
                state["selected_idea_index"] = int(ui)
                state["current_step"] = "waiting_for_approval"
                self.update_workflow_status(workflow_id, "waiting_for_approval")
                self.add_agent_result(workflow_id, "draft_agent", "Draft ready.")
                return {"required_input": {"kind": "approval"}}
            if ui == "refine":
                state["current_step"] = "start"
                return self._run_workflow_step(workflow_id, state)
        return {"status": "processing"}

    def retry_workflow_step(self, workflow_id: str, step_name: str) -> Dict[str, Any]:
        if workflow_id not in self.workflows:
            return {"error": "Workflow not found"}
        # naive reset of step
        checkpoint = self.load_checkpoint(workflow_id) or {}
        state = checkpoint.get("state", {"current_step": "start"})
        state["current_step"] = step_name
        return self.execute_workflow_step(workflow_id)
