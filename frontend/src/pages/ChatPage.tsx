import React, { useState, useEffect, useRef } from 'react';

interface ChatMessage {
  id: string;
  message: string;
  user_id: 'user' | 'ai';
  timestamp: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history from localStorage
  useEffect(() => {
    const savedMessages = localStorage.getItem('chat_history');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
  }, []);

  // Save messages to localStorage
  useEffect(() => {
    localStorage.setItem('chat_history', JSON.stringify(messages));
  }, [messages]);

  const simulateAIResponse = async (userMessage: string) => {
    setIsTyping(true);
    
    // Simulate AI thinking time
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    // Simple AI response logic
    let aiResponse = "I'm here to help you with your content creation workflows!";
    
    if (userMessage.toLowerCase().includes('hello') || userMessage.toLowerCase().includes('hi')) {
      aiResponse = "Hello! I'm your AI assistant. How can I help you today?";
    } else if (userMessage.toLowerCase().includes('workflow')) {
      aiResponse = "I can help you create and manage workflows! Try going to the Workflows page to get started.";
    } else if (userMessage.toLowerCase().includes('social media')) {
      aiResponse = "I can assist with social media content creation, LinkedIn posts, YouTube scripts, and more!";
    } else if (userMessage.toLowerCase().includes('ai') || userMessage.toLowerCase().includes('artificial intelligence')) {
      aiResponse = "AI is transforming content creation! I can help you leverage AI agents for your creative workflows.";
    } else if (userMessage.toLowerCase().includes('help')) {
      aiResponse = "I can help you with:\n• Creating content workflows\n• Managing social media content\n• Analyzing content performance\n• Finding sponsorship opportunities\n\nWhat would you like to work on?";
    }
    
    return aiResponse;
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      message: inputMessage.trim(),
      user_id: 'user',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');

    // Get AI response
    const aiResponse = await simulateAIResponse(inputMessage);
    
    const aiMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      message: aiResponse,
      user_id: 'ai',
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, aiMessage]);
    setIsTyping(false);
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('chat_history');
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">AI Chat Assistant</h1>
        <p className="text-gray-600">Chat with our AI assistant to get help with your content creation workflows.</p>
      </div>

      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Chat Header */}
        <div className="bg-primary-600 text-white p-4 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">AI Assistant</h2>
            <p className="text-primary-100 text-sm">Ready to help with your workflows</p>
          </div>
          <button
            onClick={clearChat}
            className="text-primary-100 hover:text-white text-sm underline"
          >
            Clear Chat
          </button>
        </div>

        {/* Chat Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">💬</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Start a Conversation</h3>
              <p className="text-gray-500">Ask me anything about content creation, workflows, or AI agents!</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.user_id === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.user_id === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="whitespace-pre-line">{message.message}</div>
                  <div className={`text-xs mt-2 ${
                    message.user_id === 'user' ? 'text-primary-100' : 'text-gray-500'
                  }`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))
          )}
          
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-lg">
                <div className="flex items-center space-x-1">
                  <span>AI is typing</span>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="border-t p-4">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Type your message..."
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              disabled={isTyping}
            />
            <button
              type="submit"
              disabled={isTyping || !inputMessage.trim()}
              className="bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <button
            onClick={() => setInputMessage("How do I create a workflow?")}
            className="p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow text-left"
          >
            <div className="text-2xl mb-2">⚙️</div>
            <div className="font-medium text-gray-900">Create Workflow</div>
            <div className="text-sm text-gray-600">Learn how to build your first workflow</div>
          </button>
          
          <button
            onClick={() => setInputMessage("What social media agents are available?")}
            className="p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow text-left"
          >
            <div className="text-2xl mb-2">📱</div>
            <div className="font-medium text-gray-900">Social Media</div>
            <div className="text-sm text-gray-600">Explore available AI agents</div>
          </button>
          
          <button
            onClick={() => setInputMessage("How does the AI analyze content?")}
            className="p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow text-left"
          >
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium text-gray-900">Content Analysis</div>
            <div className="text-sm text-gray-600">Understand content insights</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
