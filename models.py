from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Union, Dict, Any

class AgentResult(BaseModel):
    """Result from an agent execution"""
    agent_name: str
    result: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class AgentMessage(BaseModel):
    """Message in a workflow chat"""
    sender: str  # "user" or agent name
    content: str
    timestamp: datetime
    message_type: str = "chat"  # "chat", "agent_result", "system"
    metadata: Optional[Dict[str, Any]] = None

class WorkflowThread(BaseModel):
    """A workflow thread with its own state and memory"""
    id: str
    user_input: str
    status: str = "created"  # created, processing, completed, error
    created_at: datetime
    updated_at: Optional[datetime] = None
    agents: List[str] = []  # List of agent names that will run
    messages: List[AgentMessage] = []
    agent_results: List[AgentResult] = []
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Workflow(BaseModel):
    """A workflow definition"""
    id: str
    name: str
    description: str
    agent_sequence: List[str]  # Ordered list of agents to run
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None

class UserInput(BaseModel):
    """User input for workflow creation"""
    text: str
    workflow_type: Optional[str] = None
    platform: Optional[str] = None
    niche: Optional[str] = None
    media_url: Optional[str] = None

class WorkflowStatus(BaseModel):
    """Current status of a workflow"""
    workflow_id: str
    status: str
    current_agent: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    estimated_time_remaining: Optional[int] = None  # seconds
    last_update: datetime
    error_message: Optional[str] = None

class AgentExecutionLog(BaseModel):
    """Log of agent execution"""
    workflow_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None  # seconds

class WorkflowTemplate(BaseModel):
    """Template for creating workflows"""
    name: str
    description: str
    agent_sequence: List[str]
    default_params: Dict[str, Any] = {}
    tags: List[str] = []
    category: str = "general"

class ChatSession(BaseModel):
    """A chat session within a workflow"""
    id: str
    workflow_id: str
    user_id: str
    messages: List[AgentMessage] = []
    created_at: datetime
    last_activity: datetime
    is_active: bool = True

class WorkflowMetrics(BaseModel):
    """Metrics for workflow performance"""
    workflow_id: str
    total_execution_time: float
    agent_count: int
    success_rate: float
    average_agent_time: float
    user_satisfaction: Optional[float] = None
    created_at: datetime

class AgentCapability(BaseModel):
    """Capability of an agent"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    supported_platforms: List[str] = []
    estimated_execution_time: Optional[float] = None
    requires_human_approval: bool = False

class WorkflowExecutionRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_id: str
    user_input: UserInput
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_time: Optional[datetime] = None
    user_preferences: Optional[Dict[str, Any]] = None

class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution"""
    execution_id: str
    workflow_id: str
    status: str
    estimated_completion_time: Optional[datetime] = None
    webhook_url: Optional[str] = None
    created_at: datetime

class HumanApprovalRequest(BaseModel):
    """Request for human approval in a workflow"""
    workflow_id: str
    agent_name: str
    approval_type: str  # "content_review", "publish_confirmation", "parameter_confirmation"
    content: str
    options: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    created_at: datetime

class HumanApprovalResponse(BaseModel):
    """Response to human approval request"""
    approval_request_id: str
    approved: bool
    feedback: Optional[str] = None
    selected_option: Optional[str] = None
    user_id: str
    timestamp: datetime

class WorkflowNotification(BaseModel):
    """Notification about workflow status"""
    id: str
    workflow_id: str
    type: str  # "status_update", "completion", "error", "human_approval_needed"
    title: str
    message: str
    priority: str = "normal"
    created_at: datetime
    read: bool = False
    action_required: bool = False
