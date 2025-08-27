import React, { useState, useEffect, useRef } from 'react';
import { useWorkflow } from '../contexts/WorkflowContext';

interface WorkflowMessage {
  id: string;
  sender: string;
  content: string;
  timestamp: string;
  message_type: string;
}

interface WorkflowStatus {
  workflow_id: string;
  status: string;
  current_step: string;
  messages: WorkflowMessage[];
  content_ideas?: any[];
  post_draft?: string;
  error?: string;
}

const WorkflowPage: React.FC = () => {
  const { state, createWorkflow, dispatch, joinWorkflowRoom } = useWorkflow();
  const [newWorkflowInput, setNewWorkflowInput] = useState('');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    try {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    } catch {}
  };

  // Fetch workflow status when selected workflow changes
  useEffect(() => {
    if (selectedWorkflowId) {
      fetchWorkflowStatus(selectedWorkflowId);
    }
  }, [selectedWorkflowId]);

  const fetchWorkflowStatus = async (workflowId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/workflows/${workflowId}`);
      if (response.ok) {
        const status: WorkflowStatus = await response.json();
        setWorkflowStatus(status);
      } else {
        throw new Error(`HTTP error: ${response.status}`);
      }
    } catch (error) {
      console.error('Error fetching workflow status:', error);
      setWorkflowStatus(prev => prev ? { ...prev, error: 'Failed to fetch workflow status' } as WorkflowStatus : prev);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [workflowStatus?.messages]);

  const formatMessageContent = (content: string) => {
    return content
      .split(/(\*\*.*?\*\*|\*.*?\*)/)
      .map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={index}>{part.slice(2, -2)}</strong>;
        } else if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={index}>{part.slice(1, -1)}</em>;
        }
        return <span key={index}>{part}</span>;
      });
  };

  const handleCreateWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newWorkflowInput.trim()) {
      setIsLoading(true);
      try {
        const wid = await createWorkflow(newWorkflowInput.trim());
        setNewWorkflowInput('');
        
        // Select and join the newly created workflow immediately
        if (wid) {
          setSelectedWorkflowId(wid);
          const newW = { id: wid, user_input: newWorkflowInput.trim(), status: 'processing', agents: ['linkedin_workflow'], created_at: new Date().toISOString(), messages: [], agent_results: [] } as any;
          dispatch({ type: 'SELECT_WORKFLOW', payload: newW });
          try { joinWorkflowRoom(wid); } catch {}
          await fetchWorkflowStatus(wid);
        }
      } catch (error) {
        console.error('Error creating workflow:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = chatMessage.trim();
    if (!trimmed || !selectedWorkflowId) return;
    if (trimmed.length > 1000) {
      console.warn('Message too long');
      return;
    }
    if (trimmed) {
      setIsLoading(true);
      try {
        // Send message to the workflow
        const response = await fetch(`/api/workflows/${selectedWorkflowId}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            workflow_id: selectedWorkflowId,
            message: trimmed
          }),
        });

        if (response.ok) {
          const result = await response.json();
          
          if (result.success) {
            // Update workflow status with new messages
            await fetchWorkflowStatus(selectedWorkflowId);
          } else {
            console.error('Error from workflow:', result.error);
          }
        }
        
        setChatMessage('');
      } catch (error) {
        console.error('Error sending message:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const selectWorkflow = (workflow: any) => {
    setSelectedWorkflowId(workflow.id);
    dispatch({ type: 'SELECT_WORKFLOW', payload: workflow });
    try { joinWorkflowRoom(workflow.id); } catch (e) {}
  };

  // Ensure workflows is always an array
  const workflows = Array.isArray(state.workflows) ? state.workflows : [];
  const selectedWorkflow = workflows.find(w => w.id === selectedWorkflowId);

  // removed unused renderMessage

  const renderContentIdeas = (ideas: any[]) => {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-blue-800 mb-2">Content Ideas Generated:</h4>
        <div className="space-y-2">
          {ideas.map((idea, index) => (
            <div key={index} className="bg-white p-3 rounded border">
              <div className="font-medium">{idea.title}</div>
              <div className="text-sm text-gray-600">{idea.summary}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-sm text-blue-700">
          💡 Select an idea by typing its number (1-{ideas.length}), or ask me to refine them.
        </div>
      </div>
    );
  };

  const renderPostDraft = (draft: string) => {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-green-800 mb-2">LinkedIn Post Draft:</h4>
        <div className="bg-white p-3 rounded border whitespace-pre-wrap">{draft}</div>
        <div className="mt-3 text-sm text-green-700">
          ✍️ Type 'publish' to post this to LinkedIn, or ask me to make changes.
        </div>
      </div>
    );
  };

  const renderCurrentStep = (step: string) => {
    const stepInfo = {
      start: { title: 'Starting', description: 'Initializing workflow' },
      waiting_for_selection: { title: 'Waiting for Selection', description: 'Please select an idea' },
      drafting: { title: 'Drafting Post', description: 'Creating your LinkedIn post draft' },
      waiting_for_approval: { title: 'Waiting for Approval', description: 'Please review the draft' },
      publishing: { title: 'Publishing', description: 'Publishing your post to LinkedIn' },
      refining: { title: 'Refining', description: 'Making changes based on your feedback' },
      completed: { title: 'Completed', description: 'Workflow finished successfully' },
      error: { title: 'Error', description: 'An error occurred' },
      cancelled: { title: 'Cancelled', description: 'Workflow was cancelled' }
    } as Record<string, { title: string; description: string }>;
    
    const info = stepInfo[step as keyof typeof stepInfo] || { title: step, description: "Processing..." };
    
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-600 mr-2"></div>
          <div>
            <div className="font-medium text-yellow-800">{info.title}</div>
            <div className="text-sm text-yellow-700">{info.description}</div>
          </div>
        </div>
      </div>
    );
  };

  const renderRequiredInput = () => {
    const required = (workflowStatus as any)?.required_input || (state.selectedWorkflow as any)?.metadata?.required_input;
    if (!required || !required.kind) return null;
    if (required.kind === 'selection') {
      const options = required.options || [];
      return (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="font-medium text-blue-800 mb-2">Select an idea:</div>
          <div className="flex flex-wrap gap-2">
            {options.map((opt: any) => (
              <button key={opt.index} onClick={() => setChatMessage(String(opt.index))} className="px-3 py-1 bg-blue-600 text-white rounded">
                {opt.index}. {opt.title}
              </button>
            ))}
          </div>
        </div>
      );
    }
    if (required.kind === 'approval') {
      return (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="font-medium text-yellow-800 mb-2">Approve the draft:</div>
          <div className="flex gap-2">
            <button onClick={() => setChatMessage('publish')} className="px-3 py-1 bg-green-600 text-white rounded">Publish</button>
            <button onClick={() => setChatMessage('refine')} className="px-3 py-1 bg-gray-700 text-white rounded">Refine</button>
          </div>
        </div>
      );
    }
    if (required.kind === 'media_url') {
      return (
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
          <div className="font-medium text-purple-800 mb-2">Provide media URL (or type none):</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">LinkedIn Workflow Management</h1>
        <p className="text-gray-600">Create and manage AI-powered LinkedIn content workflows with human-in-the-loop collaboration.</p>
      </div>

      {/* Create New Workflow */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Create New LinkedIn Workflow</h2>
        <form onSubmit={handleCreateWorkflow} className="flex gap-4">
          <input
            type="text"
            value={newWorkflowInput}
            onChange={(e) => setNewWorkflowInput(e.target.value)}
            placeholder="Describe what you want to create (e.g., 'Create a LinkedIn post about AI trends')"
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {isLoading ? 'Creating...' : 'Create Workflow'}
          </button>
        </form>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Workflow List */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Active Workflows</h2>
          <div className="space-y-4">
            {workflows.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No workflows yet. Create your first one above!</p>
            ) : (
              workflows.map((workflow) => (
                <div
                  key={workflow.id}
                  onClick={() => selectWorkflow(workflow)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                    selectedWorkflowId === workflow.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-gray-900 truncate">
                      {workflow.user_input}
                    </h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      workflow.status === 'completed' ? 'bg-green-100 text-green-800' :
                      workflow.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {workflow.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500 mb-2">
                    Created: {new Date(workflow.created_at).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600">
                    Agents: {workflow.agents.length > 0 ? workflow.agents.join(', ') : 'None assigned'}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Workflow Chat */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">
            {selectedWorkflow ? 'Workflow Chat' : 'Select a Workflow'}
          </h2>
          
          {selectedWorkflow ? (
            <div className="space-y-4">
              {/* Current Step Indicator */}
              {workflowStatus?.current_step && workflowStatus.current_step !== 'unknown' && (
                renderCurrentStep(workflowStatus.current_step)
              )}
              
              {/* Content Ideas */}
              {workflowStatus?.content_ideas && workflowStatus.content_ideas.length > 0 && (
                renderContentIdeas(workflowStatus.content_ideas)
              )}
              
              {/* Post Draft */}
              {workflowStatus?.post_draft && (
                renderPostDraft(workflowStatus.post_draft)
              )}
              
              {/* Error Display */}
              {workflowStatus?.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="text-red-800">❌ Error: {workflowStatus.error}</div>
                </div>
              )}
              
              {/* Messages */}
              <div className="max-h-96 overflow-y-auto border rounded-lg p-4 bg-gray-50">
                {workflowStatus?.messages && workflowStatus.messages.length > 0 ? (
                  workflowStatus.messages.map((message) => (
                    <div key={message.id} className={`mb-4 ${message.sender === 'user' ? 'text-right' : 'text-left'}`}>
                      <div className={`inline-block max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-primary-600 text-white'
                          : message.sender === 'ai'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        <div className="text-sm font-medium mb-1">
                          {message.sender === 'user' ? 'You' : 
                           message.sender === 'ai' ? 'AI Assistant' : 
                           message.sender === 'system' ? 'System' : 'Assistant'}
                        </div>
                        <div className="whitespace-pre-wrap">
                          {formatMessageContent(message.content)}
                        </div>
                        <div className="text-xs opacity-70 mt-1">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-8">No messages yet. Start the conversation!</p>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Required Input Prompt */}
              {renderRequiredInput()}
              
              {/* Chat Input */}
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                  type="text"
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="Type your message or select an option..."
                  className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !chatMessage.trim()}
                  className="bg-primary-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </form>

              {/* Quick Actions */}
              {workflowStatus?.current_step && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-800 mb-2">💡 Quick Actions:</h4>
                  <div className="text-sm text-blue-700">
                    {workflowStatus.current_step === 'waiting_for_selection' && (
                      <div>
                        • Type a number (1-5) to select a content idea<br/>
                        • Type "refine" to generate new ideas<br/>
                        • Type "help" for assistance
                      </div>
                    )}
                    {workflowStatus.current_step === 'waiting_for_approval' && (
                      <div>
                        • Type "publish" to post to LinkedIn<br/>
                        • Type "refine" to make changes<br/>
                        • Type "new idea" to select different idea
                      </div>
                    )}
                    {workflowStatus.current_step === 'publishing' && (
                      <div>
                        • Type an image/video URL to include<br/>
                        • Type "none" for text-only post
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">💬</div>
              <p>Select a workflow from the left to start chatting with the AI agents.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkflowPage;
