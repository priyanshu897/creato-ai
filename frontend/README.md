# Creator Workflow AI - React Frontend

A modern, responsive React frontend for the Creator Workflow AI platform, featuring real-time workflow management and AI agent integration.

## 🚀 Features

- **Real-time Updates**: Live workflow status updates via Socket.IO
- **Modern UI**: Built with React 18, TypeScript, and Tailwind CSS
- **Responsive Design**: Mobile-first approach with beautiful animations
- **State Management**: Context API for global state management
- **Real-time Chat**: Human-in-the-loop interaction within workflows
- **Collapsible Sidebar**: Lindy AI-like navigation experience

## 🛠 Tech Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Socket.IO Client** - Real-time communication
- **Context API** - State management

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   └── Sidebar.tsx     # Collapsible navigation sidebar
├── contexts/           # React contexts
│   └── WorkflowContext.tsx  # Global workflow state management
├── pages/              # Page components
│   ├── Homepage.tsx    # Landing page
│   ├── WorkflowPage.tsx # Main workflow management
│   ├── SocialMediaPage.tsx # Social media agents
│   └── ChatPage.tsx    # AI chat interface
├── App.tsx             # Main app component
└── index.tsx           # Entry point
```

## 🚀 Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend server running on port 8000

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## 🔧 Configuration

The frontend is configured to proxy API requests to the backend at `http://localhost:8000`. Update the proxy in `package.json` if your backend runs on a different port.

## 🌐 Available Routes

- `/` - Homepage with platform overview
- `/workflow` - Workflow management and real-time updates
- `/social-media` - Social media agent quick actions
- `/chat` - AI chat assistant

## 🔌 Real-time Features

- **Socket.IO Integration**: Real-time workflow updates
- **Live Status Updates**: Workflow progress monitoring
- **Real-time Chat**: Human-in-the-loop interaction
- **Agent Result Streaming**: Live agent execution results

## 🎨 UI Components

### Sidebar
- Collapsible navigation
- Recent workflows display
- Platform statistics
- Smooth animations

### Workflow Management
- Create new workflows
- Real-time status updates
- Agent result display
- Integrated chat interface

### Social Media Agents
- Quick action buttons
- Agent descriptions
- Custom workflow creation

### Chat Interface
- AI assistant simulation
- Message history
- Quick action suggestions
- Local storage persistence

## 🔄 State Management

The app uses React Context API for global state management:

- **Workflow State**: All workflow data and status
- **Real-time Updates**: Socket.IO event handling
- **User Interactions**: Chat messages and workflow creation
- **Loading States**: UI feedback during operations

## 🚀 Deployment

1. **Build the app:**
   ```bash
   npm run build
   ```

2. **Serve the build folder** with your preferred web server

3. **Update backend CORS** to allow your frontend domain

## 🔧 Development

### Adding New Features

1. **Create components** in the `components/` directory
2. **Add pages** in the `pages/` directory
3. **Update routing** in `App.tsx`
4. **Extend context** in `WorkflowContext.tsx` if needed

### Styling

- Use Tailwind CSS utility classes
- Follow the established color scheme
- Maintain responsive design principles
- Add custom CSS in `index.css` if needed

## 📱 Responsive Design

The frontend is built with a mobile-first approach:

- **Mobile**: Single column layout, collapsible sidebar
- **Tablet**: Two-column layout for workflow management
- **Desktop**: Full sidebar, multi-column layouts

## 🔍 Troubleshooting

### Common Issues

1. **Socket.IO Connection Failed**
   - Ensure backend is running on port 8000
   - Check CORS configuration

2. **API Requests Failing**
   - Verify proxy configuration in package.json
   - Check backend server status

3. **Build Errors**
   - Clear node_modules and reinstall
   - Check TypeScript compilation

## 🤝 Contributing

1. Follow the existing code structure
2. Use TypeScript for all new code
3. Maintain responsive design principles
4. Test on multiple screen sizes
5. Update documentation as needed

## 📄 License

This project is part of the Creator Workflow AI platform.
