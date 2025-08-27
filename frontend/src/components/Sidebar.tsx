import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useWorkflow } from '../contexts/WorkflowContext';

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const { state } = useWorkflow();

  // Ensure workflows is always an array
  const workflows = Array.isArray(state.workflows) ? state.workflows : [];
  const recentWorkflows = workflows.slice(-5).reverse();

  const navItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/workflow', label: 'Workflows', icon: '⚙️' },
    { path: '/social-media', label: 'Social Media', icon: '📱' },
    { path: '/chat', label: 'Chat', icon: '💬' },
  ];

  return (
    <div className={`bg-dark-800 text-white transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-6">
          {!isCollapsed && (
            <h1 className="text-xl font-bold text-primary-500">Creator AI</h1>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
          >
            {isCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* Navigation */}
        <nav className="mb-8">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center p-3 rounded-lg mb-2 transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary-600 text-white'
                  : 'hover:bg-dark-700'
              }`}
            >
              <span className="text-lg mr-3">{item.icon}</span>
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Recent Workflows */}
        {!isCollapsed && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Recent Workflows</h3>
            <div className="space-y-2">
              {recentWorkflows.map((workflow) => (
                <div
                  key={workflow.id}
                  className="p-2 rounded-lg bg-dark-700 text-sm cursor-pointer hover:bg-dark-600 transition-colors"
                >
                  <div className="font-medium truncate">{workflow.user_input}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {new Date(workflow.created_at).toLocaleDateString()}
                  </div>
                  <div className={`inline-block px-2 py-1 rounded-full text-xs mt-1 ${
                    workflow.status === 'completed' ? 'bg-green-600' :
                    workflow.status === 'processing' ? 'bg-yellow-600' :
                    'bg-gray-600'
                  }`}>
                    {workflow.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        {!isCollapsed && (
          <div className="text-sm">
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Total Workflows:</span>
              <span className="font-semibold">{workflows.length}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-gray-400">Active:</span>
              <span className="font-semibold text-yellow-400">
                {workflows.filter(w => w.status === 'processing').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Completed:</span>
              <span className="font-semibold text-green-400">
                {workflows.filter(w => w.status === 'completed').length}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
