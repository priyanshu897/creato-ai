import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';
import { useState } from 'react';

// Types
export interface WorkflowThread {
  id: string;
  user_input: string;
  status: string;
  created_at: string;
  agents: string[];
  messages: any[];
  agent_results: any[];
  metadata?: any;
}

export interface AgentResult {
  id: string;
  agent_name: string;
  result: any;
  timestamp: string;
  workflow_id: string;
}

export interface AgentMessage {
  id: string;
  message: string;
  user_id: string;
  timestamp: string;
  workflow_id: string;
}

interface WorkflowState {
  workflows: WorkflowThread[];
  selectedWorkflow: WorkflowThread | null;
  loading: boolean;
  error: string | null;
}

type WorkflowAction =
  | { type: 'SET_WORKFLOWS'; payload: WorkflowThread[] }
  | { type: 'ADD_WORKFLOW'; payload: WorkflowThread }
  | { type: 'UPDATE_WORKFLOW'; payload: { id: string; updates: Partial<WorkflowThread> } }
  | { type: 'SELECT_WORKFLOW'; payload: WorkflowThread | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_AGENT_RESULT'; payload: { workflow_id: string; result: AgentResult } }
  | { type: 'ADD_MESSAGE'; payload: { workflow_id: string; message: AgentMessage } };

const initialState: WorkflowState = {
  workflows: [],
  selectedWorkflow: null,
  loading: false,
  error: null,
};

function workflowReducer(state: WorkflowState, action: WorkflowAction): WorkflowState {
  // Ensure workflows is always an array
  const currentWorkflows = Array.isArray(state.workflows) ? state.workflows : [];
  
  switch (action.type) {
    case 'SET_WORKFLOWS':
      return { ...state, workflows: Array.isArray(action.payload) ? action.payload : [] };
    case 'ADD_WORKFLOW':
      return { ...state, workflows: [...currentWorkflows, action.payload] };
    case 'UPDATE_WORKFLOW':
      return {
        ...state,
        workflows: currentWorkflows.map(w =>
          w.id === action.payload.id ? { ...w, ...action.payload.updates } : w
        ),
        selectedWorkflow: state.selectedWorkflow?.id === action.payload.id
          ? { ...state.selectedWorkflow, ...action.payload.updates }
          : state.selectedWorkflow,
      };
    case 'SELECT_WORKFLOW':
      return { ...state, selectedWorkflow: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'ADD_AGENT_RESULT':
      return {
        ...state,
        workflows: currentWorkflows.map(w =>
          w.id === action.payload.workflow_id
            ? { ...w, agent_results: [...(w.agent_results || []), action.payload.result] }
            : w
        ),
      };
    case 'ADD_MESSAGE':
      return {
        ...state,
        workflows: currentWorkflows.map(w =>
          w.id === action.payload.workflow_id
            ? { ...w, messages: [...(w.messages || []), action.payload.message] }
            : w
        ),
      };
    default:
      return state;
  }
}

interface WorkflowContextType {
  state: WorkflowState;
  createWorkflow: (userInput: string) => Promise<void>;
  sendMessage: (workflowId: string, message: string) => Promise<any>;
  getWorkflowStatus: (workflowId: string) => Promise<any>;
  joinWorkflowRoom: (workflowId: string) => void;
  dispatch: React.Dispatch<WorkflowAction>;
}

const WorkflowContext = createContext<WorkflowContextType | undefined>(undefined);

export const WorkflowProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(workflowReducer, initialState);
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    // Initialize socket connection (explicit path matches server mount "/socket.io")
    const newSocket = io('http://localhost:8000', { path: '/socket.io' });
    setSocket(newSocket);

    // Socket event handlers
    newSocket.on('connect', () => {
      console.log('Connected to workflow server');
    });

    newSocket.on('workflow_update', (data) => {
      // Persist required_input in selected workflow's metadata for UI
      dispatch({ type: 'UPDATE_WORKFLOW', payload: { id: data.workflow_id, updates: { ...data, metadata: { ...(state.selectedWorkflow?.metadata || {}), required_input: data.required_input } } } });
    });

    newSocket.on('agent_result', (data) => {
      dispatch({ type: 'ADD_AGENT_RESULT', payload: data });
    });

    newSocket.on('workflow_message', (data) => {
      dispatch({ type: 'ADD_MESSAGE', payload: data });
    });

    return () => {
      newSocket.close();
    };
  }, [state.selectedWorkflow?.metadata]);

  // Load existing workflows on mount
  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await fetch('/api/workflows');
      if (response.ok) {
        const data = await response.json();
        // Extract workflows array from the response
        const workflows = data.workflows || [];
        dispatch({ type: 'SET_WORKFLOWS', payload: workflows });
      }
    } catch (error) {
      console.error('Error fetching workflows:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to fetch workflows' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const createWorkflow = async (userInput: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const response = await fetch('/api/workflows', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_input: userInput,
          workflow_type: 'linkedin'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create workflow');
      }

      const result = await response.json();
      
      // Create workflow object
      const workflow: WorkflowThread = {
        id: result.workflow_id,
        user_input: userInput,
        status: result.status,
        created_at: new Date().toISOString(),
        agents: ['linkedin_workflow'],
        messages: [],
        agent_results: []
      };

      dispatch({ type: 'ADD_WORKFLOW', payload: workflow });
      
      // Join workflow room on socket
      if (socket) {
        socket.emit('join_workflow', { workflow_id: result.workflow_id });
      }
      
    } catch (error) {
      console.error('Error creating workflow:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create workflow' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const joinWorkflowRoom = (workflowId: string) => {
    if (socket) {
      socket.emit('join_workflow', { workflow_id: workflowId });
    }
  };

  const sendMessage = async (workflowId: string, message: string): Promise<any> => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: workflowId,
          message: message,
          user_id: 'user'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const result = await response.json();
      
      // Add message to workflow
      const messageObj: AgentMessage = {
        id: Date.now().toString(),
        message: message,
        user_id: 'user',
        timestamp: new Date().toISOString(),
        workflow_id: workflowId
      };
      
      dispatch({ type: 'ADD_MESSAGE', payload: { workflow_id: workflowId, message: messageObj } });
      
      // Update workflow status if provided
      if (result.status) {
        dispatch({ 
          type: 'UPDATE_WORKFLOW', 
          payload: { id: workflowId, updates: { status: result.status } } 
        });
      }
      
      return result;
      
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const getWorkflowStatus = async (workflowId: string): Promise<any> => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}`);
      if (response.ok) {
        return await response.json();
      }
      throw new Error('Failed to get workflow status');
    } catch (error) {
      console.error('Error getting workflow status:', error);
      throw error;
    }
  };

  const value = {
    state,
    createWorkflow,
    sendMessage,
    getWorkflowStatus,
    joinWorkflowRoom,
    dispatch,
  };

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  );
};

export function useWorkflow() {
  const context = useContext(WorkflowContext);
  if (context === undefined) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return context;
}
