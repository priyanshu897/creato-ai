import React from 'react';
import { useWorkflow } from '../contexts/WorkflowContext';

const Homepage: React.FC = () => {
  const { state } = useWorkflow();

  // Ensure workflows is always an array
  const workflows = Array.isArray(state.workflows) ? state.workflows : [];

  const stats = {
    totalWorkflows: workflows.length,
    completedWorkflows: workflows.filter(w => w.status === 'completed').length,
    processingWorkflows: workflows.filter(w => w.status === 'processing').length,
    successRate: workflows.length > 0 
      ? Math.round((workflows.filter(w => w.status === 'completed').length / workflows.length) * 100)
      : 0,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="text-center py-20 px-6">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Creator Workflow AI
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          The ultimate platform for creators to automate their content workflows with AI agents. 
          Build, manage, and execute complex workflows in real-time.
        </p>
        <div className="flex justify-center space-x-4">
          <button className="bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors">
            Get Started
          </button>
          <button className="border border-primary-600 text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors">
            Learn More
          </button>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Powerful Features for Creators
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold mb-4">AI Agent Automation</h3>
            <p className="text-gray-600">
              Intelligent agents that handle content creation, social media management, and analytics automatically.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold mb-4">Real-time Workflows</h3>
            <p className="text-gray-600">
              Monitor and interact with workflows in real-time with live updates and human-in-the-loop capabilities.
            </p>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-4">Advanced Analytics</h3>
            <p className="text-gray-600">
              Track performance, optimize workflows, and gain insights into your content creation process.
            </p>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Platform Statistics
          </h2>
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-primary-600 mb-2">{stats.totalWorkflows}</div>
              <div className="text-gray-600">Total Workflows</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-green-600 mb-2">{stats.completedWorkflows}</div>
              <div className="text-gray-600">Completed</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-yellow-600 mb-2">{stats.processingWorkflows}</div>
              <div className="text-gray-600">In Progress</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">{stats.successRate}%</div>
              <div className="text-gray-600">Success Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-primary-600 py-16">
        <div className="max-w-4xl mx-auto text-center px-6">
          <h2 className="text-3xl font-bold text-white mb-6">
            Ready to Transform Your Content Creation?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join thousands of creators who are already automating their workflows with AI.
          </p>
          <button className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
            Start Building Workflows
          </button>
        </div>
      </div>
    </div>
  );
};

export default Homepage;
