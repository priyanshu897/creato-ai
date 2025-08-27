import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from models import WorkflowThread, AgentResult, AgentMessage
import json

class WorkflowManager:
    def __init__(self):
        self.workflows: Dict[str, WorkflowThread] = {}
        self.workflow_status: Dict[str, str] = {}
        self.agent_results: Dict[str, List[AgentResult]] = {}
        self.workflow_messages: Dict[str, List[AgentMessage]] = {}
        
    def add_workflow(self, workflow: WorkflowThread):
        """Add a new workflow to the manager"""
        self.workflows[workflow.id] = workflow
        self.workflow_status[workflow.id] = workflow.status
        self.agent_results[workflow.id] = []
        self.workflow_messages[workflow.id] = []
        
        print(f"Added workflow {workflow.id}: {workflow.user_input}")
        
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
