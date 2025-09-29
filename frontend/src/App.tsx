import React from 'react';
import { AppProvider, useApp } from './contexts/AppContext';
import FileUpload from './components/FileUpload';
import LoadingScreen from './components/LoadingScreen';
import Chat from './components/Chat';

function AppContent() {
  const { state } = useApp();

  const renderCurrentView = () => {
    switch (state) {
      case 'upload':
        return <FileUpload />;
      case 'loading':
        return <LoadingScreen />;
      case 'chat':
        return <Chat />;
      default:
        return <FileUpload />;
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg">
      {renderCurrentView()}
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;