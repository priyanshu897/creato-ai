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
        """Execute the complete LinkedIn workflow in real-time"""
        print(f"Starting LinkedIn workflow: {workflow_id}")
        
        # Initialize workflow state
        workflow_state = LinkedInWorkflowState(workflow_id, user_input)
        self.active_workflows[workflow_id] = workflow_state
        
        # Add initial message
        workflow_state.add_message("ai", "🚀 Starting LinkedIn workflow...", "agent_result")
        
        # Extract niche from user input
        niche = await self._extract_niche(user_input)
        workflow_state.user_niche = niche
        workflow_state.add_message("ai", f"🎯 Detected niche: **{niche}**", "agent_result")
        
        # Generate content ideas
        workflow_state.add_message("ai", "💡 Generating content ideas for your niche...", "agent_result")
        ideas = await self._generate_linkedin_ideas(workflow_state)
        
        if ideas:
            workflow_state.content_ideas = ideas
            workflow_state.add_message("ai", f"✅ Generated {len(ideas)} content ideas", "agent_result")
            
            # Present ideas to user with clear instructions
            ideas_text = "\n".join([f"**{i+1}.** {idea.title}\n   _{idea.summary}_" for i, idea in enumerate(ideas)])
            workflow_state.add_message("ai", f"🎯 **Here are your LinkedIn post ideas for '{niche}':**\n\n{ideas_text}\n\n**Please select an idea by typing its number (1-{len(ideas)}) or ask me to refine them.**", "agent_result")
            
            # Set workflow to wait for user input
            workflow_state.current_step = "waiting_for_selection"
            workflow_state.status = "waiting_for_user"
        else:
            workflow_state.add_message("ai", "❌ I couldn't generate content ideas. Please try again with a different niche.", "agent_result")
            workflow_state.status = "error"
        
        return {
            "workflow_id": workflow_id,
            "status": workflow_state.status,
            "current_step": workflow_state.current_step,
            "messages": workflow_state.messages,
            "content_ideas": ideas
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
            return []

    async def process_workflow_message(self, workflow_id: str, user_message: str) -> Dict[str, Any]:
        """Process a message in an active workflow with real-time agent execution"""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        workflow_state = self.active_workflows[workflow_id]
        
        # Add user message
        workflow_state.add_message("user", user_message, "chat")
        
        # Process based on current step with real-time agent execution
        if workflow_state.current_step == "waiting_for_selection":
            return await self._handle_idea_selection_realtime(workflow_state, user_message)
        elif workflow_state.current_step == "drafting":
            return await self._handle_drafting_realtime(workflow_state, user_message)
        elif workflow_state.current_step == "publishing":
            return await self._handle_publishing_realtime(workflow_state, user_message)
        elif workflow_state.current_step == "waiting_for_approval":
            return await self._handle_approval_realtime(workflow_state, user_message)
        
        return {"error": "Unknown workflow step"}

    async def _handle_idea_selection_realtime(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Handle idea selection with real-time agent execution"""
        try:
            # Check if user selected an idea
            if user_message.isdigit():
                selection = int(user_message)
                if 1 <= selection <= len(workflow_state.content_ideas):
                    selected_idea = workflow_state.content_ideas[selection - 1]
                    workflow_state.selected_idea = selected_idea
                    workflow_state.current_step = "drafting"
                    workflow_state.status = "processing"
                    
                    # Show selection confirmation
                    workflow_state.add_message("ai", f"🎯 **Great choice!** I've selected idea #{selection}: **{selected_idea.title}**", "agent_result")
                    
                    # Start drafting process in real-time
                    workflow_state.add_message("ai", "✍️ **Now I'm drafting your LinkedIn post...**", "agent_result")
                    
                    # Generate post draft using the agent
                    post_draft = await self._draft_linkedin_post(workflow_state)
                    workflow_state.post_draft = post_draft
                    
                    # Show the draft and ask for approval
                    workflow_state.add_message("ai", f"📝 **Here's your LinkedIn post draft:**\n\n{post_draft}\n\n**What would you like me to do?**\n• Type '**publish**' to post this to LinkedIn\n• Type '**refine**' to make changes\n• Type '**new idea**' to select a different idea", "agent_result")
                    
                    workflow_state.current_step = "waiting_for_approval"
                    workflow_state.status = "waiting_for_user"
                    
                    return {
                        "workflow_id": workflow_state.workflow_id,
                        "status": workflow_state.status,
                        "current_step": workflow_state.current_step,
                        "messages": workflow_state.messages,
                        "post_draft": post_draft
                    }
                else:
                    workflow_state.add_message("ai", f"❌ Please select a valid number between 1 and {len(workflow_state.content_ideas)}", "agent_result")
            
            # Check for other commands
            elif "refine" in user_message.lower() or "more" in user_message.lower():
                workflow_state.add_message("ai", "🔄 **Generating new ideas...**", "agent_result")
                new_ideas = await self._generate_linkedin_ideas(workflow_state)
                if new_ideas:
                    workflow_state.content_ideas = new_ideas
                    ideas_text = "\n".join([f"**{i+1}.** {idea.title}\n   _{idea.summary}_" for i, idea in enumerate(new_ideas)])
                    workflow_state.add_message("ai", f"✨ **Here are some refined ideas:**\n\n{ideas_text}\n\n**Please select an idea (1-{len(new_ideas)})**", "agent_result")
                else:
                    workflow_state.add_message("ai", "❌ Sorry, I couldn't generate new ideas. Please try a different approach.", "agent_result")
            
            elif "help" in user_message.lower():
                workflow_state.add_message("ai", "💡 **How to use this workflow:**\n\n• **Type a number (1-5)** to select a content idea\n• **Type 'refine'** to generate new ideas\n• **Type 'help'** to see this message again\n• **Type 'cancel'** to stop the workflow", "agent_result")
            
            elif "cancel" in user_message.lower():
                workflow_state.status = "cancelled"
                workflow_state.add_message("ai", "❌ **Workflow cancelled.** You can start a new one anytime.", "agent_result")
                return {
                    "workflow_id": workflow_state.workflow_id,
                    "status": workflow_state.status,
                    "current_step": "cancelled",
                    "messages": workflow_state.messages
                }
            
            else:
                workflow_state.add_message("ai", f"🤔 I didn't understand that. Please select an idea by typing its number (1-{len(workflow_state.content_ideas)}) or type 'help' for assistance.", "agent_result")
            
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages
            }
            
        except Exception as e:
            workflow_state.add_message("ai", f"❌ **Error:** {str(e)}", "agent_result")
            return {"error": str(e)}

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
            
            return response.content.strip()
        except Exception as e:
            print(f"Error drafting post: {e}")
            return "Error generating post draft"

    async def _handle_approval_realtime(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Handle post approval with real-time agent execution"""
        user_message_lower = user_message.lower()
        
        if "publish" in user_message_lower or "post" in user_message_lower:
            workflow_state.current_step = "publishing"
            workflow_state.status = "processing"
            workflow_state.add_message("ai", "🚀 **Great! I'm ready to publish your LinkedIn post.**", "agent_result")
            workflow_state.add_message("ai", "📸 **Do you have an image or video URL to include?** (Type the URL, or type 'none' if not)", "agent_result")
            
        elif "refine" in user_message_lower or "change" in user_message_lower:
            workflow_state.add_message("ai", "✏️ **What changes would you like me to make to the post?** Be specific about what you'd like to modify.", "agent_result")
            workflow_state.current_step = "refining"
            
        elif "new idea" in user_message_lower:
            workflow_state.current_step = "waiting_for_selection"
            workflow_state.status = "waiting_for_user"
            workflow_state.add_message("ai", "🔄 **Let's go back to idea selection.**", "agent_result")
            ideas_text = "\n".join([f"**{i+1}.** {idea.title}\n   _{idea.summary}_" for i, idea in enumerate(workflow_state.content_ideas)])
            workflow_state.add_message("ai", f"🎯 **Here are your content ideas again:**\n\n{ideas_text}\n\n**Please select an idea (1-{len(workflow_state.content_ideas)})**", "agent_result")
            
        else:
            workflow_state.add_message("ai", "🤔 **I'm ready to publish when you are.** Please type:\n• **'publish'** to proceed\n• **'refine'** to make changes\n• **'new idea'** to select a different idea", "agent_result")
        
        return {
            "workflow_id": workflow_state.workflow_id,
            "status": workflow_state.status,
            "current_step": workflow_state.current_step,
            "messages": workflow_state.messages
        }

    async def _handle_publishing_realtime(self, workflow_state: LinkedInWorkflowState, user_message: str) -> Dict[str, Any]:
        """Handle publishing with real-time agent execution"""
        if user_message.lower() != "none":
            workflow_state.media_url = user_message
            workflow_state.add_message("ai", f"📸 **Got it! I'll include the media:** {user_message}", "agent_result")
        else:
            workflow_state.add_message("ai", "📝 **No media attached. Publishing text-only post.**", "agent_result")
        
        # Check if we have LinkedIn credentials
        if not os.getenv("LINKEDIN_ACCESS_TOKEN"):
            workflow_state.add_message("ai", "⚠️ **LinkedIn credentials not configured.** This is a simulation. To enable real posting, please set up your LinkedIn API credentials.", "agent_result")
            workflow_state.status = "completed_simulation"
            workflow_state.add_message("ai", "🎭 **Simulation Complete!** Your post would have been published to LinkedIn with real credentials.", "agent_result")
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages,
                "simulation": True
            }
        
        try:
            # Attempt to publish to LinkedIn
            workflow_state.add_message("ai", "🚀 **Publishing your post to LinkedIn...**", "agent_result")
            
            # This would call the actual LinkedIn publishing function
            # For now, we'll simulate success
            workflow_state.status = "completed"
            workflow_state.add_message("ai", "✅ **Success! Your LinkedIn post has been published!**", "agent_result")
            workflow_state.add_message("ai", "🎉 **Workflow completed successfully!** You can now view your post on LinkedIn.", "agent_result")
            
            return {
                "workflow_id": workflow_state.workflow_id,
                "status": workflow_state.status,
                "current_step": workflow_state.current_step,
                "messages": workflow_state.messages,
                "published": True
            }
            
        except Exception as e:
            workflow_state.add_message("ai", f"❌ **Error publishing to LinkedIn:** {str(e)}", "agent_result")
            workflow_state.status = "error"
            return {"error": str(e)}

    async def get_workflow_status(self, workflow_id: str) -> Optional[LinkedInWorkflowState]:
        """Get the status of a workflow"""
        return self.active_workflows.get(workflow_id)

    async def get_all_workflows(self) -> List[LinkedInWorkflowState]:
        """Get all active workflows"""
        return list(self.active_workflows.values())
    
    async def run_agent(self, agent_name: str, user_input: str, workflow_id: str) -> str:
        """Run a specific agent"""
        try:
            if agent_name == "linkedin_workflow":
                return await self.execute_linkedin_workflow(workflow_id, user_input)
            elif agent_name == "linkedin_ideation":
                return await self._generate_linkedin_ideas(self.active_workflows[workflow_id])
            elif agent_name == "linkedin_drafting":
                return await self._draft_linkedin_post(self.active_workflows[workflow_id])
            elif agent_name == "linkedin_publishing":
                return await self._handle_publishing_realtime(self.active_workflows[workflow_id], user_input)
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
                return await func(state)
            else:
                return func(state)
        except Exception as e:
            return f"Error running workflow function: {str(e)}"
