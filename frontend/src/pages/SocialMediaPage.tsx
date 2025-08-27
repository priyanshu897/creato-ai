import React from 'react';
import { useWorkflow } from '../contexts/WorkflowContext';

const SocialMediaPage: React.FC = () => {
  const { createWorkflow } = useWorkflow();

  const agents = [
    {
      name: 'LinkedIn Ideation',
      description: 'Generate creative content ideas for LinkedIn',
      icon: '💡',
      action: 'Create LinkedIn content ideas about AI trends',
    },
    {
      name: 'LinkedIn Drafting',
      description: 'Draft engaging LinkedIn posts',
      icon: '✍️',
      action: 'Draft a LinkedIn post about artificial intelligence',
    },
    {
      name: 'LinkedIn Publishing',
      description: 'Publish content to LinkedIn',
      icon: '🚀',
      action: 'Publish a LinkedIn post about AI',
    },
    {
      name: 'YouTube Script',
      description: 'Create video scripts for YouTube',
      icon: '🎬',
      action: 'Create a YouTube script about AI technology',
    },
    {
      name: 'Content Analysis',
      description: 'Analyze content performance',
      icon: '📊',
      action: 'Analyze my recent content performance',
    },
    {
      name: 'Sponsorship Finder',
      description: 'Find sponsorship opportunities',
      icon: '💰',
      action: 'Find sponsorship opportunities for AI content',
    },
  ];

  const handleQuickAction = async (action: string) => {
    await createWorkflow(action);
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Social Media Management</h1>
        <p className="text-gray-600">Quick access to AI agents for social media content creation and management.</p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="text-4xl mb-4">{agent.icon}</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">{agent.name}</h3>
            <p className="text-gray-600 mb-4">{agent.description}</p>
            <button
              onClick={() => handleQuickAction(agent.action)}
              className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Quick Action
            </button>
          </div>
        ))}
      </div>

      <div className="mt-12 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Something Custom?</h2>
        <p className="text-gray-600 mb-6">
          Can't find the right agent? Create a custom workflow by describing exactly what you need.
        </p>
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Describe your custom workflow..."
            className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button className="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors">
            Create Custom
          </button>
        </div>
      </div>
    </div>
  );
};

export default SocialMediaPage;
