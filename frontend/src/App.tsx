import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Homepage from './pages/Homepage';
import WorkflowPage from './pages/WorkflowPage';
import SocialMediaPage from './pages/SocialMediaPage';
import ChatPage from './pages/ChatPage';
import { WorkflowProvider } from './contexts/WorkflowContext';

function App() {
  return (
    <WorkflowProvider>
      <Router>
        <div className="flex h-screen bg-gray-50">
          <Sidebar />
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<Homepage />} />
              <Route path="/workflow" element={<WorkflowPage />} />
              <Route path="/social-media" element={<SocialMediaPage />} />
              <Route path="/chat" element={<ChatPage />} />
            </Routes>
          </main>
        </div>
      </Router>
    </WorkflowProvider>
  );
}

export default App;
