import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
from pydantic import BaseModel
import uvicorn

from workflow_manager import WorkflowManager
from agent_runner import AgentRunner
from database import DatabaseManager
from models import Workflow, WorkflowThread, AgentMessage, UserInput

# Global managers
workflow_manager = WorkflowManager()
agent_runner = AgentRunner()
db_manager = DatabaseManager()

# Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode='asgi')

# FastAPI app
app = FastAPI(
    title="Creator Workflow AI",
    description="A Lindy AI-like platform for creators with workflow management and agent automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join_workflow(sid, data):
    workflow_id = data.get('workflow_id')
    if workflow_id:
        await sio.enter_room(sid, workflow_id)
        await sio.emit('joined_workflow', {
            'workflow_id': workflow_id,
            'message': f'Joined workflow {workflow_id}'
        }, room=sid)

@sio.event
async def chat_message(sid, data):
    workflow_id = data.get('workflow_id')
    message = data.get('message')
    
    if workflow_id and message:
        # Add message to workflow
        workflow_manager.add_message(workflow_id, message, "user")
        
        # Process with agents
        asyncio.create_task(process_chat_message(workflow_id, message))

# API Models
class CreateWorkflowRequest(BaseModel):
    user_input: str
    workflow_type: Optional[str] = None

class WorkflowResponse(BaseModel):
    workflow_id: str
    status: str
    message: str

class ChatMessage(BaseModel):
    workflow_id: str
    message: str
    user_id: str = "user"

class WorkflowMessageResponse(BaseModel):
    workflow_id: str
    status: str
    current_step: str
    messages: List[Dict]
    content_ideas: Optional[List[Dict]] = None
    post_draft: Optional[str] = None
    error: Optional[str] = None
    required_input: Optional[Dict] = None

class WorkflowMessageRequest(BaseModel):
    workflow_id: str
    message: str

# Routes
@app.get("/")
async def get_homepage():
    return JSONResponse({"message": "Creator Workflow AI API", "status": "running"})

# API Endpoints
@app.post("/api/workflows", response_model=WorkflowResponse)
async def create_workflow(request: CreateWorkflowRequest):
    """Create a new workflow based on user input"""
    try:
        print("[API] create_workflow called", {"user_input": request.user_input, "workflow_type": request.workflow_type})
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        # Analyze input and determine agents
        selected_agents = await agent_runner.analyze_input(request.user_input)
        
        # Create workflow thread
        workflow_thread = WorkflowThread(
            id=workflow_id,
            user_input=request.user_input,
            status="processing",
            created_at=datetime.utcnow(),
            agents=selected_agents,
            messages=[],
            agent_results=[]
        )
        
        # Add to workflow manager
        workflow_manager.add_workflow(workflow_thread)
        
        # Execute the workflow
        if "linkedin_workflow" in selected_agents:
            workflow_result = await agent_runner.execute_linkedin_workflow(workflow_id, request.user_input)
            try:
                print("[Agent] execute_linkedin_workflow result keys:", list(workflow_result.keys()))
                print("[Agent] required_input:", workflow_result.get("required_input"))
            except Exception:
                pass
            
            # Update workflow with results
            if "content_ideas" in workflow_result:
                workflow_manager.add_agent_result(
                    workflow_id, 
                    "LinkedIn Workflow", 
                    f"Generated {len(workflow_result['content_ideas'])} content ideas"
                )
            
            # Add messages to workflow and emit in real-time
            if "messages" in workflow_result:
                for msg in workflow_result["messages"]:
                    if msg["sender"] != "system":
                        workflow_manager.add_message(
                            workflow_id, 
                            msg["content"], 
                            msg["sender"]
                        )
                # Emit messages
                _emit_workflow_messages(workflow_result["messages"], workflow_id)
            
            _emit_workflow_update(workflow_id, workflow_result.get("status"), workflow_result.get("current_step"), workflow_result.get("required_input"))
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="processing",
            message="Workflow created and started successfully"
        )
        
    except Exception as e:
        print(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflows/{workflowId}/chat")
async def send_workflow_message(workflowId: str, message: WorkflowMessageRequest):
    """Send a message to an active workflow"""
    try:
        print("[API] chat called", {"workflow_id": workflowId, "message": message.message})
        # Add user message to workflow manager
        workflow_manager.add_message(workflowId, "user", message.message)
        
        # Check if this is a LinkedIn workflow and process it
        workflow = workflow_manager.get_workflow(workflowId)
        if workflow and "linkedin_workflow" in workflow.get("agents", []):
            # Process the message through the agent runner
            result = await agent_runner.process_workflow_message(workflowId, message.message)
            try:
                print("[Agent] process_workflow_message result keys:", list(result.keys()))
                print("[Agent] required_input:", result.get("required_input"))
            except Exception:
                pass
            
            if "error" not in result:
                # Update workflow manager with new messages and status
                workflow_manager.update_workflow(workflowId, {
                    "status": result.get("status", "processing"),
                    "current_step": result.get("current_step", "unknown"),
                    "messages": result.get("messages", [])
                })
                
                # Emit messages and updates to clients in real-time
                if result.get("messages"):
                    _emit_workflow_messages(result["messages"], workflowId)
                _emit_workflow_update(workflowId, result.get("status"), result.get("current_step"), result.get("required_input"))
                
                return {
                    "success": True,
                    "workflow_id": workflowId,
                    "status": result.get("status"),
                    "current_step": result.get("current_step"),
                    "messages": result.get("messages", []),
                    "required_input": result.get("required_input")
                }
            else:
                return {"error": result["error"]}
        else:
            # For non-LinkedIn workflows, just add the message
            return {"success": True, "message": "Message added to workflow"}
            
    except Exception as e:
        print(f"Error processing workflow message: {e}")
        return {"error": str(e)}

@app.get("/api/workflows/{workflow_id}", response_model=WorkflowMessageResponse)
async def get_workflow_status(workflow_id: str):
    """Get the current status and messages of a workflow"""
    try:
        # Check if workflow exists
        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get workflow state from agent runner if it's a LinkedIn workflow
        if "linkedin_workflow" in workflow.agents:
            workflow_state = await agent_runner.get_workflow_status(workflow_id)
            if workflow_state:
                return WorkflowMessageResponse(
                    workflow_id=workflow_id,
                    status=workflow_state.status,
                    current_step=workflow_state.current_step,
                    messages=workflow_state.messages,
                    content_ideas=workflow_state.content_ideas,
                    post_draft=workflow_state.post_draft,
                    error=workflow_state.error
                )
        
        # Fallback to workflow manager data
        return WorkflowMessageResponse(
            workflow_id=workflow_id,
            status=workflow.status,
            current_step="unknown",
            messages=workflow_manager.get_workflow_messages(workflow_id),
            error=None
        )
        
    except Exception as e:
        print(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflows")
async def get_all_workflows():
    """Get all workflows"""
    try:
        workflows = workflow_manager.get_all_workflows()
        return {"workflows": workflows}
    except Exception as e:
        print(f"Error getting workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background tasks
async def process_workflow(workflow_id: str, user_input: str):
    """Process a workflow with agents"""
    try:
        # Update status
        workflow_manager.update_workflow_status(workflow_id, "processing")
        
        # Analyze user input and determine agents to run
        agents_to_run = await agent_runner.analyze_input(user_input)
        
        # Run agents sequentially
        for agent_name in agents_to_run:
            workflow_manager.update_workflow_status(workflow_id, f"Running {agent_name}")
            
            # Run agent
            result = await agent_runner.run_agent(agent_name, user_input, workflow_id)
            
            # Add result to workflow
            workflow_manager.add_agent_result(workflow_id, agent_name, result)
            
                    # Broadcast update via Socket.IO
        await sio.emit('workflow_update', {
            'workflow_id': workflow_id,
            'agent': agent_name,
            'result': result,
            'status': 'completed'
        }, room=workflow_id)
        
        # Mark workflow as completed
        workflow_manager.update_workflow_status(workflow_id, "completed")
        
        # Broadcast completion via Socket.IO
        await sio.emit('workflow_completed', {
            'workflow_id': workflow_id,
            'message': 'Workflow completed successfully'
        }, room=workflow_id)
        
    except Exception as e:
        workflow_manager.update_workflow_status(workflow_id, f"error: {str(e)}")
        await sio.emit('workflow_error', {
            'workflow_id': workflow_id,
            'error': str(e)
        }, room=workflow_id)

async def process_chat_message(workflow_id: str, message: str):
    """Process a chat message with agents if needed"""
    try:
        # Check if message requires agent processing
        if await agent_runner.needs_agent_processing(message):
            # Run appropriate agent
            agent_name = await agent_runner.determine_agent(message)
            result = await agent_runner.run_agent(agent_name, message, workflow_id)
            
            # Add result to workflow
            workflow_manager.add_agent_result(workflow_id, agent_name, result)
            
                    # Broadcast update via Socket.IO
        await sio.emit('chat_response', {
            'workflow_id': workflow_id,
            'agent': agent_name,
            'response': result
        }, room=workflow_id)
    
    except Exception as e:
        print(f"Error processing chat message: {e}")

def _emit_workflow_messages(messages: List[Dict], workflow_id: str):
    # Emit each non-user message to the specific workflow room
    async def _emit_all():
        for msg in messages:
            if msg.get("sender") != "user":
                await sio.emit('workflow_message', {
                    'workflow_id': workflow_id,
                    'message': msg
                }, room=workflow_id)
    asyncio.create_task(_emit_all())


def _emit_workflow_update(workflow_id: str, status: Optional[str] = None, current_step: Optional[str] = None, required_input: Optional[Dict] = None):
    async def _emit():
        await sio.emit('workflow_update', {
            'workflow_id': workflow_id,
            'status': status,
            'current_step': current_step,
            'required_input': required_input,
        }, room=workflow_id)
    asyncio.create_task(_emit())

# Build combined ASGI app for Socket.IO + FastAPI
combined_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    uvicorn.run(combined_app, host="0.0.0.0", port=8000)
