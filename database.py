import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from models import WorkflowThread, AgentResult, AgentMessage, Workflow

class DatabaseManager:
    """Simple in-memory database manager for workflows"""
    
    def __init__(self, storage_file: str = "workflow_data.json"):
        self.storage_file = storage_file
        self.workflows: Dict[str, WorkflowThread] = {}
        self.workflow_templates: Dict[str, Workflow] = {}
        self.agent_results: Dict[str, List[AgentResult]] = {}
        self.messages: Dict[str, List[AgentMessage]] = {}
        
        # Load existing data if available
        self.load_data()
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default workflow templates"""
        default_templates = {
            "linkedin_posting": Workflow(
                id="linkedin_posting_template",
                name="LinkedIn Posting Workflow",
                description="Complete workflow for creating and publishing LinkedIn posts",
                agent_sequence=["linkedin_ideation", "linkedin_drafting", "linkedin_publishing"],
                created_at=datetime.now(timezone.utc),
                metadata={
                    "platform": "linkedin",
                    "category": "social_media",
                    "estimated_time": "5-10 minutes"
                }
            ),
            "youtube_content": Workflow(
                id="youtube_content_template",
                name="YouTube Content Creation",
                description="Workflow for creating YouTube video scripts and publishing",
                agent_sequence=["youtube_script", "youtube_publishing"],
                created_at=datetime.now(timezone.utc),
                metadata={
                    "platform": "youtube",
                    "category": "video_content",
                    "estimated_time": "15-30 minutes"
                }
            ),
            "content_analysis": Workflow(
                id="content_analysis_template",
                name="Content Analysis Workflow",
                description="Analyze content performance and trends",
                agent_sequence=["content_analysis"],
                created_at=datetime.now(timezone.utc),
                metadata={
                    "platform": "multi",
                    "category": "analytics",
                    "estimated_time": "2-5 minutes"
                }
            )
        }
        
        for template_id, template in default_templates.items():
            self.workflow_templates[template_id] = template
    
    def save_workflow(self, workflow: WorkflowThread) -> bool:
        """Save a workflow to storage"""
        try:
            self.workflows[workflow.id] = workflow
            self.save_data()
            return True
        except Exception as e:
            print(f"Error saving workflow: {e}")
            return False
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowThread]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def get_all_workflows(self) -> List[WorkflowThread]:
        """Get all workflows"""
        return list(self.workflows.values())
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """Update a workflow with new data"""
        if workflow_id not in self.workflows:
            return False
        
        try:
            workflow = self.workflows[workflow_id]
            for key, value in updates.items():
                if hasattr(workflow, key):
                    setattr(workflow, key, value)
            
            workflow.updated_at = datetime.now(timezone.utc)
            self.save_data()
            return True
        except Exception as e:
            print(f"Error updating workflow: {e}")
            return False
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        try:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
            
            if workflow_id in self.agent_results:
                del self.agent_results[workflow_id]
            
            if workflow_id in self.messages:
                del self.messages[workflow_id]
            
            self.save_data()
            return True
        except Exception as e:
            print(f"Error deleting workflow: {e}")
            return False
    
    def add_agent_result(self, workflow_id: str, agent_result: AgentResult) -> bool:
        """Add an agent result to a workflow"""
        try:
            if workflow_id not in self.agent_results:
                self.agent_results[workflow_id] = []
            
            self.agent_results[workflow_id].append(agent_result)
            self.save_data()
            return True
        except Exception as e:
            print(f"Error adding agent result: {e}")
            return False
    
    def get_agent_results(self, workflow_id: str) -> List[AgentResult]:
        """Get all agent results for a workflow"""
        return self.agent_results.get(workflow_id, [])
    
    def add_message(self, workflow_id: str, message: AgentMessage) -> bool:
        """Add a message to a workflow"""
        try:
            if workflow_id not in self.messages:
                self.messages[workflow_id] = []
            
            self.messages[workflow_id].append(message)
            self.save_data()
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            return False
    
    def get_messages(self, workflow_id: str) -> List[AgentMessage]:
        """Get all messages for a workflow"""
        return self.messages.get(workflow_id, [])
    
    def get_workflow_templates(self) -> List[Workflow]:
        """Get all available workflow templates"""
        return list(self.workflow_templates.values())
    
    def get_workflow_template(self, template_id: str) -> Optional[Workflow]:
        """Get a specific workflow template"""
        return self.workflow_templates.get(template_id)
    
    def create_workflow_from_template(self, template_id: str, user_input: str) -> Optional[WorkflowThread]:
        """Create a new workflow from a template"""
        template = self.get_workflow_template(template_id)
        if not template:
            return None
        
        try:
            workflow = WorkflowThread(
                id=f"workflow_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                user_input=user_input,
                status="created",
                created_at=datetime.now(timezone.utc),
                agents=template.agent_sequence.copy(),
                messages=[],
                agent_results=[],
                metadata={
                    "template_id": template_id,
                    "template_name": template.name,
                    "category": template.metadata.get("category", "general")
                }
            )
            
            self.save_workflow(workflow)
            return workflow
        except Exception as e:
            print(f"Error creating workflow from template: {e}")
            return None
    
    def search_workflows(self, query: str, category: Optional[str] = None) -> List[WorkflowThread]:
        """Search workflows by query and category"""
        results = []
        query_lower = query.lower()
        
        for workflow in self.workflows.values():
            # Check if query matches user input or metadata
            if (query_lower in workflow.user_input.lower() or
                (workflow.metadata and 
                 any(query_lower in str(value).lower() for value in workflow.metadata.values()))):
                
                # Filter by category if specified
                if category is None or (workflow.metadata and 
                                      workflow.metadata.get("category") == category):
                    results.append(workflow)
        
        return results
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics about workflows"""
        total_workflows = len(self.workflows)
        completed_workflows = sum(1 for w in self.workflows.values() if w.status == "completed")
        processing_workflows = sum(1 for w in self.workflows.values() if w.status == "processing")
        error_workflows = sum(1 for w in self.workflows.values() if "error" in w.status)
        
        total_agents_run = sum(len(self.agent_results.get(w.id, [])) for w in self.workflows.values())
        total_messages = sum(len(self.messages.get(w.id, [])) for w in self.workflows.values())
        
        # Calculate average execution time (if available)
        execution_times = []
        for workflow in self.workflows.values():
            if workflow.status == "completed" and workflow.updated_at:
                duration = (workflow.updated_at - workflow.created_at).total_seconds()
                execution_times.append(duration)
        
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "processing_workflows": processing_workflows,
            "error_workflows": error_workflows,
            "total_agents_run": total_agents_run,
            "total_messages": total_messages,
            "success_rate": (completed_workflows / total_workflows * 100) if total_workflows > 0 else 0,
            "average_execution_time": avg_execution_time,
            "templates_available": len(self.workflow_templates)
        }
    
    def save_data(self):
        """Save data to storage file"""
        try:
            data = {
                "workflows": {wid: w.dict() for wid, w in self.workflows.items()},
                "agent_results": {wid: [ar.model_dump() for ar in ars] for wid, ars in self.agent_results.items()},
                "messages": {wid: [m.dict() for m in msgs] for wid, msgs in self.messages.items()},
                "templates": {tid: t.dict() for tid, t in self.workflow_templates.items()},
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def load_data(self):
        """Load data from storage file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                # Load workflows
                for wid, w_data in data.get("workflows", {}).items():
                    try:
                        workflow = WorkflowThread(**w_data)
                        self.workflows[wid] = workflow
                    except Exception as e:
                        print(f"Error loading workflow {wid}: {e}")
                
                # Load agent results
                for wid, ar_data in data.get("agent_results", {}).items():
                    try:
                        self.agent_results[wid] = [AgentResult(**ar) for ar in ar_data]
                    except Exception as e:
                        print(f"Error loading agent results for {wid}: {e}")
                
                # Load messages
                for wid, msg_data in data.get("messages", {}).items():
                    try:
                        self.messages[wid] = [AgentMessage(**msg) for msg in msg_data]
                    except Exception as e:
                        print(f"Error loading messages for {wid}: {e}")
                
                print(f"Loaded {len(self.workflows)} workflows from storage")
                
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old workflow data"""
        cutoff_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
        
        workflows_to_delete = []
        for workflow_id, workflow in self.workflows.items():
            if workflow.created_at < cutoff_date:
                workflows_to_delete.append(workflow_id)
        
        for workflow_id in workflows_to_delete:
            self.delete_workflow(workflow_id)
        
        print(f"Cleaned up {len(workflows_to_delete)} old workflows")
        self.save_data()
