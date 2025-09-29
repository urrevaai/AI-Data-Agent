import React from 'react';
import { FiLoader, FiDatabase, FiCpu, FiBarChart } from 'react-icons/fi';

const LoadingScreen: React.FC = () => {
  const steps = [
    { icon: FiDatabase, text: 'Processing your file...', delay: 0 },
    { icon: FiCpu, text: 'Analyzing data patterns...', delay: 1000 },
    { icon: FiBarChart, text: 'Preparing visualizations...', delay: 2000 },
  ];

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="mb-8">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <FiLoader className="w-20 h-20 text-primary-blue animate-spin" />
          </div>
          <h2 className="text-2xl font-bold text-primary-text mb-2">
            Processing Your Data
          </h2>
          <p className="text-primary-muted">
            This usually takes a few seconds
          </p>
        </div>

        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className="flex items-center space-x-3 p-3 bg-dark-card rounded-lg opacity-50 animate-pulse"
              style={{ animationDelay: `${step.delay}ms` }}
            >
              <step.icon className="w-5 h-5 text-primary-blue flex-shrink-0" />
              <span className="text-primary-text">{step.text}</span>
            </div>
          ))}
        </div>

        <div className="mt-8">
          <div className="w-full bg-dark-border rounded-full h-2">
            <div className="bg-primary-blue h-2 rounded-full animate-pulse w-2/3"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;