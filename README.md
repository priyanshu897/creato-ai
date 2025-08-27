# Creator Workflow AI 🚀

A Lindy AI-like platform for creators with workflow management, AI-powered agents, and human-in-the-loop capabilities. Automate your content creation workflow with intelligent agents that handle LinkedIn posting, YouTube scripting, content analysis, and more.

## ✨ Features

- **🤖 AI-Powered Agents**: Intelligent agents for content creation, publishing, and analysis
- **🔄 Workflow Automation**: Create complex multi-step workflows with real-time progress tracking
- **💬 Human-in-the-Loop**: Seamlessly collaborate with AI agents through chat interfaces
- **📱 Multi-Platform Support**: LinkedIn, YouTube, and other social media platforms
- **📊 Real-Time Updates**: WebSocket-based real-time communication and progress tracking
- **🎨 Modern UI**: Beautiful, responsive interface inspired by Lindy AI
- **🧵 Workflow Threads**: Manage multiple workflows simultaneously with individual chat sessions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   AI Agents     │
│   (HTML/CSS/JS) │◄──►│   Backend       │◄──►│   (LangChain)   │
│                 │    │   + WebSockets  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# Required: Your Groq API key for LLM functionality
GROQ_API_KEY=your_groq_api_key_here

# Optional: LinkedIn OAuth credentials for publishing
LINKEDIN_CLIENT_ID=your_linkedin_client_id_here
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret_here

# Optional: Server configuration
HOST=0.0.0.0
PORT=8000
```

### 3. Start the Application

**Windows:**
```bash
start.bat
```

**Manual:**
```bash
python main.py
```

### 4. Access the Platform

- **Homepage**: `http://localhost:8000/`
- **Workflows**: `http://localhost:8000/workflow`
- **Social Media**: `http://localhost:8000/social-media`
- **Chat**: `http://localhost:8000/chat`
- **API Docs**: `http://localhost:8000/docs`

## 🎯 How It Works

### 1. **Create Workflows**
Type natural language requests like:
- "Create a LinkedIn post about AI trends and publish it"
- "Write a YouTube script about digital marketing"
- "Analyze my content performance and suggest improvements"

### 2. **AI Agent Execution**
The system automatically:
- Analyzes your request
- Determines which agents to run
- Executes agents in sequence
- Provides real-time progress updates

### 3. **Human Collaboration**
- Chat with agents during workflow execution
- Provide feedback and approvals
- Intervene when needed
- Monitor progress in real-time

### 4. **Workflow Management**
- View all active workflows
- Switch between workflow threads
- Access chat history for each workflow
- Track agent performance and results

## 🤖 Available Agents

### **LinkedIn Agents**
- **Ideation Agent**: Generate content ideas based on niche
- **Drafting Agent**: Create engaging post drafts
- **Publishing Agent**: Publish content to LinkedIn

### **YouTube Agents**
- **Script Agent**: Generate video scripts
- **Publishing Agent**: Upload and publish videos

### **Analysis Agents**
- **Content Analysis**: Analyze performance and trends
- **Sponsorship Agent**: Find brand partnership opportunities

## 🔧 API Endpoints

### **Core Workflow Endpoints**
- `POST /api/workflows` - Create new workflow
- `GET /api/workflows` - List all workflows
- `GET /api/workflows/{id}` - Get specific workflow
- `POST /api/workflows/{id}/chat` - Send chat message to workflow

### **WebSocket Endpoints**
- `WS /ws/{connection_id}` - Real-time communication

## 📁 Project Structure

```
creatoAI/
├── main.py                 # FastAPI application entry point
├── workflow_manager.py     # Workflow management and state
├── agent_runner.py         # AI agent execution engine
├── database.py             # Data persistence layer
├── models.py               # Pydantic data models
├── templates/              # HTML templates
│   ├── homepage.html      # Landing page
│   ├── workflow.html      # Main workflow interface
│   ├── social_media.html  # Social media management
│   └── chat.html          # General chat interface
├── social_media_agents/   # Existing agent implementations
├── requirements.txt        # Python dependencies
├── start.bat              # Windows startup script
└── README.md              # This file
```

## 🎨 UI Features

### **Responsive Design**
- Mobile-first approach
- Collapsible sidebar
- Modern gradient backgrounds
- Interactive components

### **Real-Time Updates**
- WebSocket-based communication
- Live progress tracking
- Instant notifications
- Real-time chat

### **Workflow Visualization**
- Progress bars
- Agent status indicators
- Timeline views
- Chat integration

## 🔌 Integration

### **Existing Social Media Agents**
The platform integrates with your existing `social_media_agents` directory:
- LinkedIn ideation and publishing workflows
- YouTube script generation
- Content analysis capabilities
- Sponsorship finding

### **Extending the Platform**
To add new agents:
1. Implement agent logic in `agent_runner.py`
2. Add agent configuration
3. Update frontend templates
4. Test integration

## 🚀 Deployment

### **Development**
```bash
python main.py
```

### **Production**
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000

# With gunicorn (Linux/Mac)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Environment Variables**
- `GROQ_API_KEY`: Required for LLM functionality
- `LINKEDIN_CLIENT_ID`: For LinkedIn publishing
- `LINKEDIN_CLIENT_SECRET`: For LinkedIn OAuth
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)

## 🐛 Troubleshooting

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <process_id> /F
   
   # Mac/Linux
   lsof -i :8000
   kill -9 <process_id>
   ```

2. **Module Not Found**
   ```bash
   pip install -r requirements.txt
   ```

3. **API Key Issues**
   - Verify `.env` file exists
   - Check `GROQ_API_KEY` is set correctly
   - Ensure API key has sufficient credits

4. **WebSocket Connection Issues**
   - Check if server is running
   - Verify browser supports WebSockets
   - Check console for error messages

### **Debug Mode**
Enable debug logging by setting environment variable:
```bash
export PYTHONPATH=.
python main.py
```

## 🔮 Future Enhancements

- **Multi-User Support**: User authentication and management
- **Advanced Analytics**: Detailed workflow performance metrics
- **Template Library**: Pre-built workflow templates
- **API Integrations**: More social media platforms
- **Mobile App**: Native mobile application
- **Advanced AI**: More sophisticated agent capabilities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check server logs for errors
4. Open an issue in the repository

---

**Happy Content Creating! 🚀**

*Built with ❤️ for creators who want to automate their workflow*
