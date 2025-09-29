import React, { useState, useRef, useEffect } from 'react';
import { FiSend, FiUser, FiCpu, FiLoader } from 'react-icons/fi';
import axios from 'axios';
import { useApp } from '../contexts/AppContext';
import Visualization from './Visualization';

const Chat: React.FC = () => {
  const { uploadId, messages, addMessage, isProcessing, setProcessing } = useApp();
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !uploadId || isProcessing) return;

    const question = inputValue.trim();
    setInputValue('');
    setProcessing(true);

    // Add user message
    addMessage({
      type: 'user',
      content: question,
    });

    try {
      const response = await axios.post('http://127.0.0.1:8000/query', {
        question,
        upload_id: uploadId,
      });

      const { natural_language_answer, query_result_data, visualization_suggestion } = response.data;

      // Add AI response
      addMessage({
        type: 'ai',
        content: natural_language_answer,
        visualization: query_result_data && visualization_suggestion ? {
          type: visualization_suggestion.chart_type?.toLowerCase() || 'table',
          data: query_result_data,
          suggestion: `${visualization_suggestion.chart_type} chart showing ${visualization_suggestion.x_axis} vs ${visualization_suggestion.y_axis || 'values'}`,
        } : undefined,
      });
    } catch (error) {
      console.error('Query failed:', error);
      addMessage({
        type: 'ai',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col">
      {/* Header */}
      <div className="bg-dark-card border-b border-dark-border p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-semibold text-primary-text">AI Data Agent</h1>
          <p className="text-sm text-primary-muted">Ask questions about your data</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <FiCpu className="w-12 h-12 mx-auto text-primary-muted mb-4" />
              <h3 className="text-lg font-medium text-primary-text mb-2">
                Ready to analyze your data!
              </h3>
              <p className="text-primary-muted">
                Ask me anything about your uploaded file. I can help with summaries, trends, insights, and more.
              </p>
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                {[
                  "What are the key insights from this data?",
                  "Show me the top performing categories",
                  "What trends can you identify?",
                  "Create a summary of the main findings"
                ].map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(suggestion)}
                    className="p-3 bg-dark-card hover:bg-dark-hover border border-dark-border rounded-lg text-left text-sm text-primary-muted hover:text-primary-text transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.type === 'ai' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-primary-blue rounded-full flex items-center justify-center">
                    <FiCpu className="w-4 h-4 text-white" />
                  </div>
                </div>
              )}

              <div className={`max-w-3xl ${message.type === 'user' ? 'order-first' : ''}`}>
                <div
                  className={`rounded-lg p-4 ${
                    message.type === 'user'
                      ? 'bg-primary-blue text-white ml-auto max-w-lg'
                      : 'bg-dark-card border border-dark-border'
                  }`}
                >
                  <p className={`${message.type === 'user' ? 'text-white' : 'text-primary-text'} whitespace-pre-wrap`}>
                    {message.content}
                  </p>
                </div>

                {message.visualization && (
                  <div className="mt-4">
                    <Visualization
                      type={message.visualization.type}
                      data={message.visualization.data}
                      suggestion={message.visualization.suggestion}
                    />
                  </div>
                )}

                <div className="flex items-center gap-2 mt-2 text-xs text-primary-muted">
                  <span>{message.timestamp.toLocaleTimeString()}</span>
                </div>
              </div>

              {message.type === 'user' && (
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-dark-hover rounded-full flex items-center justify-center">
                    <FiUser className="w-4 h-4 text-primary-muted" />
                  </div>
                </div>
              )}
            </div>
          ))}

          {isProcessing && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-blue rounded-full flex items-center justify-center">
                  <FiCpu className="w-4 h-4 text-white" />
                </div>
              </div>
              <div className="max-w-3xl">
                <div className="bg-dark-card border border-dark-border rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <FiLoader className="w-4 h-4 text-primary-blue animate-spin" />
                    <span className="text-primary-muted">Thinking...</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-dark-card border-t border-dark-border p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question about your data..."
              disabled={isProcessing}
              className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-primary-text placeholder-primary-muted focus:outline-none focus:ring-2 focus:ring-primary-blue focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isProcessing}
              className="px-6 py-3 bg-primary-blue text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 focus:ring-offset-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <FiSend className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;