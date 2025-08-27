import asyncio
import re
from typing import List, Dict, Optional, Any
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

# Import existing social media agents
try:
    from social_media_agents.ideation_workflow_alpha import (
        IdeasList, Idea, draft_linkedin_post, draft_youtube_script,
        upload_media_to_linkedin, publish_to_linkedin, AgentState
    )
    from social_media_agents.publishing_agent import app as youtube_publishing_app
    from social_media_agents.analysis_agent import build_graph as build_analysis_graph
    from social_media_agents.sponsorship_agent import app as sponsorship_app
except ImportError as e:
    print(f"Warning: Could not import some social media agents: {e}")
    # Create mock functions for testing
    def draft_linkedin_post(state): return {"post_draft": "Mock LinkedIn post"}
    def draft_youtube_script(state): return {"script_draft": "Mock YouTube script"}
    def upload_media_to_linkedin(state): return {"media_asset_urn": "mock_urn"}
    def publish_to_linkedin(state): return {"success": True, "post_id": "mock_id"}

# Load environment variables
load_dotenv()

class AgentConfig(BaseModel):
    name: str
    description: str
    keywords: List[str]
    function_name: str
    required_params: List[str]

class LinkedInWorkflowState:
    """State management for LinkedIn workflow execution"""
    def __init__(self, workflow_id: str, user_input: str):
        self.workflow_id = workflow_id
        self.user_input = user_input
        self.current_step = "start"
        self.user_niche = ""
        self.platform_choice = "linkedin"
        self.content_ideas = None
        self.selected_idea = None
        self.post_draft = None
        self.media_url = None
        self.media_asset_urn = None
        self.error = None
        self.messages = []
        self.status = "processing"
        
    def add_message(self, sender: str, content: str, message_type: str = "agent_result"):
        """Add a message to the workflow"""
        message = {
            "id": str(uuid.uuid4()),
            "sender": sender,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type": message_type
        }
        self.messages.append(message)
        return message

class AgentRunner:
    def __init__(self):
        self.agents = self._initialize_agents()
        self.llm = ChatGroq(model="llama3-8b-8192", temperature=0.5)
        self.active_workflows: Dict[str, LinkedInWorkflowState] = {}
        
    def _initialize_agents(self) -> Dict[str, AgentConfig]:
        """Initialize available agents"""
        return {
            "linkedin_workflow": AgentConfig(
                name="LinkedIn Complete Workflow",
                description="Complete LinkedIn workflow from ideation to publishing",
                keywords=["linkedin", "post", "workflow", "publish", "complete"],
                function_name="execute_linkedin_workflow",
                required_params=["user_input"]
            ),
            "linkedin_ideation": AgentConfig(
                name="LinkedIn Ideation Agent",
                description="Generates content ideas for LinkedIn posts",
                keywords=["linkedin", "post", "content", "idea", "social media"],
                function_name="generate_linkedin_ideas",
                required_params=["user_niche", "platform_choice"]
            ),
            "linkedin_drafting": AgentConfig(
                name="LinkedIn Drafting Agent",
                description="Creates draft LinkedIn posts from ideas",
                keywords=["linkedin", "draft", "write", "post", "content"],
                function_name="draft_linkedin_post",
                required_params=["selected_idea", "niche"]
            ),
            "linkedin_publishing": AgentConfig(
                name="LinkedIn Publishing Agent",
                description="Publishes content to LinkedIn",
                keywords=["linkedin", "publish", "post", "upload", "share"],
                function_name="publish_to_linkedin",
                required_params=["post_draft", "media_url"]
            ),
            "youtube_script": AgentConfig(
                name="YouTube Script Agent",
                description="Creates YouTube video scripts",
                keywords=["youtube", "script", "video", "content", "script"],
                function_name="draft_youtube_script",
                required_params=["selected_idea", "niche"]
            ),
            "youtube_publishing": AgentConfig(
                name="YouTube Publishing Agent",
                description="Publishes content to YouTube",
                keywords=["youtube", "publish", "video", "upload", "share"],
                function_name="publish_to_youtube",
                required_params=["video_file", "title", "description"]
            ),
            "content_analysis": AgentConfig(
                name="Content Analysis Agent",
                description="Analyzes content performance and trends",
                keywords=["analysis", "trend", "performance", "insights", "metrics"],
                function_name="analyze_content",
                required_params=["content_url", "platform"]
            ),
            "sponsorship_agent": AgentConfig(
                name="Sponsorship Agent",
                description="Finds sponsorship opportunities",
                keywords=["sponsorship", "brand", "partnership", "monetization"],
                function_name="find_sponsorships",
                required_params=["niche", "audience_size"]
            )
        }
    
    async def analyze_input(self, user_input: str) -> List[str]:
        """Analyze user input and determine which agents to run"""
        print(f"Analyzing input: {user_input}")
        
        # Check if this is a LinkedIn workflow request
        linkedin_keywords = ["linkedin", "post", "publish", "share"]
        if any(keyword in user_input.lower() for keyword in linkedin_keywords):
            return ["linkedin_workflow"]
        
        # Check for other agent types
        selected_agents = []
        for agent_id, agent in self.agents.items():
            if any(keyword in user_input.lower() for keyword in agent.keywords):
                selected_agents.append(agent_id)
        
        return selected_agents if selected_agents else ["linkedin_workflow"]

    async def execute_linkedin_workflow(self, workflow_id: str, user_input: str) -> Dict[str, Any]:
        """Execute the complete LinkedIn workflow"""
        print(f"Starting LinkedIn workflow: {workflow_id}")
        
        # Initialize workflow state
        workflow_state = LinkedInWorkflowState(workflow_id, user_input)
        self.active_workflows[workflow_id] = workflow_state
        
        # Add initial message
        workflow_state.add_message("system", "Starting LinkedIn workflow...", "system")
        
        # Extract niche from user input
        niche = await self._extract_niche(user_input)
        workflow_state.user_niche = niche
        workflow_state.add_message("system", f"Detected niche: {niche}", "system")
        
        # Generate content ideas
        ideas = await self._generate_linkedin_ideas(workflow_state)
        if ideas:
            workflow_state.content_ideas = ideas
            workflow_state.add_message("system", f"Generated {len(ideas)} content ideas", "system")
            
            # Present ideas to user
            ideas_text = "\n".join([f"{i+1}. {idea.title}" for i, idea in enumerate(ideas)])
            workflow_state.add_message("ai", f"Here are some LinkedIn post ideas for '{niche}':\n\n{ideas_text}\n\nPlease select an idea (1-{len(ideas)}) or ask me to refine them.", "agent_result")
            workflow_state.current_step = "waiting_for_selection"
            workflow_state.status = "waiting_for_user"
        else:
            workflow_state.add_message("ai", "I couldn't generate content ideas. Please try again with a different niche.", "agent_result")
            workflow_state.status = "error"
        
        return {
            "workflow_id": workflow_id,
            "status": workflow_state.status,
            "current_step": workflow_state.current_step,
            "messages": workflow_state.messages,
            "content_ideas": ideas,
            "required_input": {
                "kind": "selection" if ideas else None,
                "options": [
                    {"index": i+1, "title": idea.title}
                    for i, idea in enumerate(ideas or [])
                ]
            }
        }

    async def _extract_niche(self, user_input: str) -> str:
        """Extract niche from user input using LLM"""
        try:
            prompt = PromptTemplate(
                template="Extract the main topic or niche from this user input. Return only the topic, nothing else.\n\nUser input: {user_input}",
                input_variables=["user_input"]
            )
            chain = prompt | self.llm
            response = await chain.ainvoke({"user_input": user_input})
            return response.content.strip()
        except Exception as e:
            print(f"Error extracting niche: {e}")
            return "general content"

    async def _generate_linkedin_ideas(self, workflow_state: LinkedInWorkflowState) -> List[Idea]:
        """Generate LinkedIn content ideas"""
        try:
            parser = JsonOutputParser(pydantic_object=IdeasList)
            prompt = PromptTemplate(
                template="""
                You are a content trend analyst for LinkedIn.
                Based on the niche: {user_niche}, generate 5 highly engaging post ideas.
                Return ONLY a JSON object that adheres strictly to the following schema. Do NOT include any conversational text, code block syntax, or any other formatting.
                
                {format_instructions}
                """,
                input_variables=["user_niche"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )
            chain = prompt | self.llm | parser
            ideas_dict = await chain.ainvoke({"user_niche": workflow_state.user_niche})
            
            if ideas_dict and "ideas" in ideas_dict:
                return [Idea(**idea) for idea in ideas_dict["ideas"]]
            return []
        except Exception as e:
            print(f"Error generating ideas: {e}")
            # Surface error into chat so the user can retry
            try:
                workflow_state.add_message("ai", "❌ Failed to generate ideas. Please try again.", "agent_result")
            except Exception:
                pass
            return []

    async def _draft_linkedin_post(self, workflow_state: LinkedInWorkflowState) -> str:
        """Draft a LinkedIn post using the agent"""
        try:
            prompt = PromptTemplate(
                template="""
                You are a master copywriter for LinkedIn.
                Based on the following idea, draft a professional and engaging LinkedIn post.
                Use relevant hashtags and a clear call to action.
                Return ONLY the post text and nothing else.
                
                Idea: {idea_title} - {idea_summary}
                """,
                input_variables=["idea_title", "idea_summary"],
            )
            
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "idea_title": workflow_state.selected_idea.title,
                "idea_summary": workflow_state.selected_idea.summary,
            })
            try:
                print("[LLM draft_linkedin_post raw]:", response.content[:400])
            except Exception:
                pass
            return response.content.strip()
        except Exception as e:
            print(f"Error drafting post: {e}")
            return "Error generating post draft"

    async def _handle_approval_realtime(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Handle post drafting step"""
        if "publish" in user_message.lower() or "post" in user_message.lower():
            workflow_state.current_step = "publishing"
            workflow_state.add_message("ai", "Great! I'm ready to publish your LinkedIn post. Do you have an image or video URL to include? (Type 'none' if not)", "agent_result")
        elif "change" in user_message.lower() or "edit" in user_message.lower():
            workflow_state.add_message("ai", "What changes would you like me to make to the post?", "agent_result")
            workflow_state.current_step = "refining"
        else:
            workflow_state.add_message("ai", "I'm ready to publish your post when you are. Type 'publish' to proceed, or let me know what changes you'd like.", "agent_result")
        
        return {
            "workflow_id": workflow_state.workflow_id,
            "status": workflow_state.status,
            "current_step": workflow_state.current_step,
            "messages": workflow_state.messages
        }

    async def _handle_publishing(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Handle publishing step"""
        if user_message:
            media_input = user_message.strip()
            if media_input.lower() != "none":
                # Basic URL validation
                if not re.match(r"^https?://", media_input):
                    workflow_state.add_message("ai", "⚠️ Please provide a valid image/video URL or type 'none'.", "agent_result")
                    return {
                        "workflow_id": workflow_state.workflow_id,
                        "status": workflow_state.status,
                        "current_step": workflow_state.current_step,
                        "messages": workflow_state.messages
                    }
                workflow_state.media_url = media_input
                workflow_state.add_message("ai", f"Got it! I'll include the media: {media_input}", "agent_result")
        
        # Require LinkedIn credentials for real posting
        if not os.getenv("LINKEDIN_ACCESS_TOKEN"):
            workflow_state.add_message("ai", "❌ LinkedIn credentials not configured (LINKEDIN_ACCESS_TOKEN).", "agent_result")
            workflow_state.status = "error"
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages,
                "error": "Missing LinkedIn credentials"
            }
        
        try:
            # Attempt to publish to LinkedIn
            workflow_state.add_message("ai", "Publishing your post to LinkedIn...", "agent_result")
            # If media URL present, attempt upload to LinkedIn using real function
            if workflow_state.media_url:
                try:
                    agent_state = self._to_agent_state_dict(workflow_state)
                    upload_res = await self._safe_call(upload_media_to_linkedin, agent_state)
                    try:
                        print("[Agent upload_media_to_linkedin output]:", upload_res)
                    except Exception:
                        pass
                    if isinstance(upload_res, dict):
                        self._merge_agent_state(workflow_state, upload_res)
                except Exception as up_e:
                    workflow_state.add_message("ai", f"⚠️ Media upload failed, proceeding without media. ({up_e})", "agent_result")
            
            # Call the real LinkedIn publishing function
            agent_state = self._to_agent_state_dict(workflow_state)
            publish_res = await self._safe_call(publish_to_linkedin, agent_state)
            try:
                print("[Agent publish_to_linkedin output]:", publish_res)
            except Exception:
                pass
            if isinstance(publish_res, dict) and publish_res.get("error"):
                workflow_state.add_message("ai", f"❌ Error publishing to LinkedIn: {publish_res['error']}", "agent_result")
                workflow_state.status = "error"
                return {"error": publish_res["error"]}

            workflow_state.status = "completed"
            workflow_state.add_message("ai", "✅ Your LinkedIn post has been published successfully!", "agent_result")
            
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages,
                "published": True
            }
            
        except Exception as e:
            workflow_state.add_message("ai", f"❌ Error publishing to LinkedIn: {str(e)}", "agent_result")
            workflow_state.status = "error"
            return {"error": str(e)}

    def _to_agent_state_dict(self, s: LinkedInWorkflowState) -> Dict[str, Any]:
        return {
            "user_niche": s.user_niche,
            "platform_choice": "linkedin",
            "content_ideas": s.content_ideas,
            "selected_idea": s.selected_idea,
            "post_draft": s.post_draft,
            "script_draft": None,
            "user_input": "publish",
            "error": s.error,
            "media_url": s.media_url,
            "media_asset_urn": s.media_asset_urn,
        }

    def _merge_agent_state(self, s: LinkedInWorkflowState, agent_state: Dict[str, Any]) -> None:
        s.media_asset_urn = agent_state.get("media_asset_urn", s.media_asset_urn)
        s.post_draft = agent_state.get("post_draft", s.post_draft)
        s.error = agent_state.get("error", s.error)

    async def _handle_refining_realtime(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Refine the drafted post based on user instructions using LLM"""
        if not workflow_state.post_draft:
            workflow_state.add_message("ai", "There's no draft to refine yet. Please select an idea first.", "agent_result")
            workflow_state.current_step = "waiting_for_selection"
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages
            }
        try:
            prompt = PromptTemplate(
                template=(
                    "You are editing a LinkedIn post. Apply the user's requested changes to improve the draft.\n"
                    "Keep the tone professional and engaging. Return only the revised post text.\n\n"
                    "Original draft:\n{draft}\n\nUser requests:\n{instructions}\n"
                ),
                input_variables=["draft", "instructions"],
            )
            chain = prompt | self.llm
            with asyncio.timeout(60):
                resp = await chain.ainvoke({
                    "draft": workflow_state.post_draft,
                    "instructions": user_message,
                })
            workflow_state.post_draft = resp.content.strip()
            workflow_state.add_message("ai", f"📝 Here's the updated draft:\n\n{workflow_state.post_draft}\n\nType 'publish' to post, or give more changes.", "agent_result")
            workflow_state.current_step = "waiting_for_approval"
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages,
                "post_draft": workflow_state.post_draft
            }
        except Exception as e:
            workflow_state.add_message("ai", f"❌ Failed to refine the draft: {e}", "agent_result")
            return {"error": str(e)}

    async def process_workflow_message(self, workflow_id: str, user_message: str) -> Dict[str, Any]:
        """Process a message in an active LinkedIn workflow with step routing and validation."""
        state = self.active_workflows.get(workflow_id)
        if not state:
            return {"error": "Workflow not found", "status": "error"}
        # Record user message
        state.add_message("user", user_message, "chat")
        step = state.current_step or "start"
        try:
            if step in ("start", "waiting_for_selection"):
                # Selection or commands
                text = user_message.strip().lower()
                if text.isdigit() and state.content_ideas:
                    idx = int(text)
                    if 1 <= idx <= len(state.content_ideas):
                        state.selected_idea = state.content_ideas[idx - 1]
                        state.add_message("ai", f"Selected idea #{idx}: {state.selected_idea.title}", "agent_result")
                        # Draft post
                        state.add_message("ai", "Drafting your LinkedIn post...", "agent_result")
                        draft = await self._draft_linkedin_post(state)
                        state.post_draft = draft
                        state.current_step = "waiting_for_approval"
                        state.status = "waiting_for_user"
                        state.add_message("ai", f"Draft ready. Type 'publish' or describe changes.", "agent_result")
                        return {
                            "workflow_id": state.workflow_id,
                            "status": state.status,
                            "current_step": state.current_step,
                            "messages": state.messages,
                            "post_draft": state.post_draft,
                            "required_input": {"kind": "approval"}
                        }
                    else:
                        state.add_message("ai", f"Please enter a number between 1 and {len(state.content_ideas)}.", "agent_result")
                elif "refine" in text or "more" in text:
                    # Regenerate ideas
                    state.add_message("ai", "Generating new ideas...", "agent_result")
                    new_ideas = await self._generate_linkedin_ideas(state)
                    state.content_ideas = new_ideas
                    if new_ideas:
                        ideas_text = "\n".join([f"{i+1}. {idea.title}" for i, idea in enumerate(new_ideas)])
                        state.add_message("ai", f"Here are some refined ideas:\n\n{ideas_text}\n\nSelect 1-{len(new_ideas)}.", "agent_result")
                        return {
                            "workflow_id": state.workflow_id,
                            "status": state.status,
                            "current_step": state.current_step,
                            "messages": state.messages,
                            "content_ideas": state.content_ideas,
                            "required_input": {
                                "kind": "selection",
                                "options": [
                                    {"index": i+1, "title": idea.title}
                                    for i, idea in enumerate(new_ideas)
                                ]
                            }
                        }
                    else:
                        state.add_message("ai", "Couldn't generate new ideas. Try different instructions.", "agent_result")
                else:
                    state.add_message("ai", "Please select an idea by number, or type 'refine'.", "agent_result")
                    return {
                        "workflow_id": state.workflow_id,
                        "status": state.status,
                        "current_step": state.current_step,
                        "messages": state.messages,
                        "content_ideas": state.content_ideas,
                        "required_input": {
                            "kind": "selection",
                            "options": [
                                {"index": i+1, "title": idea.title}
                                for i, idea in enumerate(state.content_ideas or [])
                            ]
                        }
                    }
            elif step == "waiting_for_approval":
                res = await self._handle_approval_realtime(state, user_message)
                if res and not res.get("required_input") and state.current_step == "publishing":
                    res["required_input"] = {"kind": "media_url"}
                return res
            elif step == "refining":
                return await self._handle_refining_realtime(state, user_message)
            elif step == "publishing":
                return await self._handle_publishing(state, user_message)

            return {
                "workflow_id": state.workflow_id,
                "status": state.status,
                "current_step": state.current_step,
                "messages": state.messages,
                "post_draft": state.post_draft,
                "content_ideas": state.content_ideas,
            }
        except Exception as e:
            state.add_message("ai", f"❌ Error: {e}", "agent_result")
            state.status = "error"
            return {"error": str(e)}

    async def _safe_call(self, func, state):
        """Call external workflow function with timeout and error capture."""
        try:
            with asyncio.timeout(60):
                if asyncio.iscoroutinefunction(func):
                    return await func(state)
                return func(state)
        except Exception as e:
            return {"error": str(e)}

    async def get_workflow_status(self, workflow_id: str) -> Optional[LinkedInWorkflowState]:
        """Get the status of a workflow"""
        return self.active_workflows.get(workflow_id)

    async def get_all_workflows(self) -> List[LinkedInWorkflowState]:
        """Get all active workflows"""
        return list(self.active_workflows.values())
    
    async def run_agent(self, agent_name: str, user_input: str, workflow_id: str) -> str:
        """Run a specific agent with the given input"""
        if agent_name not in self.agents:
            return f"Error: Agent {agent_name} not found"
        
        agent_config = self.agents[agent_name]
        print(f"Running agent: {agent_name}")
        
        try:
            if agent_name == "linkedin_workflow":
                return await self.execute_linkedin_workflow(workflow_id, user_input)
            elif agent_name == "linkedin_ideation":
                return await self._generate_linkedin_ideas(self.active_workflows[workflow_id])
            elif agent_name == "linkedin_drafting":
                return await self._draft_linkedin_post(self.active_workflows[workflow_id])
            elif agent_name == "linkedin_publishing":
                return await self._handle_publishing(self.active_workflows[workflow_id], user_input)
            elif agent_name == "youtube_script":
                return await self._run_workflow_function(draft_youtube_script, self.active_workflows[workflow_id])
            elif agent_name == "youtube_publishing":
                return await self._run_workflow_function(publish_to_linkedin, self.active_workflows[workflow_id])
            elif agent_name == "content_analysis":
                return await self._run_workflow_function(build_analysis_graph, self.active_workflows[workflow_id])
            elif agent_name == "sponsorship_agent":
                return await self._run_workflow_function(sponsorship_app.app.run, self.active_workflows[workflow_id])
            else:
                return f"Agent {agent_name} not implemented yet"
                
        except Exception as e:
            error_msg = f"Error running agent {agent_name}: {str(e)}"
            print(error_msg)
            return error_msg
    
    async def _run_workflow_function(self, func, state):
        """Helper to run workflow functions"""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(state)
            else:
                result = func(state)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_niche(self, user_input: str) -> str:
        """Extract niche from user input"""
        niches = ["ai", "technology", "marketing", "business", "health", "fitness", "cooking", "travel"]
        user_input_lower = user_input.lower()
        
        for niche in niches:
            if niche in user_input_lower:
                return niche
        
        return "general"
    
    def _extract_idea(self, user_input: str) -> str:
        """Extract content idea from user input"""
        # Simple extraction - could be improved with LLM
        if "ai" in user_input.lower():
            return "AI trends and insights"
        elif "marketing" in user_input.lower():
            return "Digital marketing strategies"
        else:
            return "Content creation tips"
    
    def _extract_post_content(self, user_input: str) -> str:
        """Extract post content from user input"""
        # This would be more sophisticated in practice
        return user_input
    
    def _extract_media_url(self, user_input: str) -> str:
        """Extract media URL from user input"""
        # Simple URL extraction
        url_match = re.search(r'https?://[^\s]+', user_input)
        return url_match.group(0) if url_match else None
    
    async def needs_agent_processing(self, message: str) -> bool:
        """Determine if a message needs agent processing"""
        # Simple keyword-based detection
        agent_keywords = ["analyze", "generate", "create", "post", "publish", "draft"]
        return any(keyword in message.lower() for keyword in agent_keywords)
    
    async def determine_agent(self, message: str) -> str:
        """Determine which agent should process a message"""
        message_lower = message.lower()
        
        if "linkedin" in message_lower:
            if "idea" in message_lower:
                return "linkedin_ideation"
            elif "draft" in message_lower:
                return "linkedin_drafting"
            elif "publish" in message_lower:
                return "linkedin_publishing"
        
        elif "youtube" in message_lower:
            if "script" in message_lower:
                return "youtube_script"
            elif "publish" in message_lower:
                return "youtube_publishing"
        
        elif "analyze" in message_lower:
            return "content_analysis"
        
        elif "sponsorship" in message_lower:
            return "sponsorship_agent"
        
        # Default to ideation
        return "linkedin_ideation"
    
    def get_agent_info(self) -> Dict[str, Dict]:
        """Get information about all available agents"""
        return {
            name: {
                "description": agent.description,
                "keywords": agent.keywords,
                "required_params": agent.required_params
            }
            for name, agent in self.agents.items()
        }
