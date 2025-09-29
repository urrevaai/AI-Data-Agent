import React, { createContext, useContext, useReducer, ReactNode } from 'react';

export type AppState = 'upload' | 'loading' | 'chat';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  visualization?: {
    type: 'bar' | 'line' | 'pie' | 'table';
    data: any[];
    suggestion: string;
    // New fields for data key mapping
    xAxisKey?: string; // Key for X-axis in bar/line charts (e.g., 'product_category')
    yAxisKey?: string; // Key for Y-axis/value in bar/line charts (e.g., 'total_sales_value')
    pieKey?: string;   // Key for values in pie chart (e.g., 'total_sales_value')
    pieNameKey?: string; // Key for names/labels in pie chart (e.g., 'product_category')
  };
  timestamp: Date;
}

interface AppContextType {
  state: AppState;
  uploadId: string | null;
  messages: Message[];
  isProcessing: boolean;
  setState: (state: AppState) => void;
  setUploadId: (id: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setProcessing: (processing: boolean) => void;
  clearMessages: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface Action {
  type: 'SET_STATE' | 'SET_UPLOAD_ID' | 'ADD_MESSAGE' | 'SET_PROCESSING' | 'CLEAR_MESSAGES';
  payload?: any;
}

interface State {
  appState: AppState;
  uploadId: string | null;
  messages: Message[];
  isProcessing: boolean;
}

function appReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_STATE':
      return { ...state, appState: action.payload };
    case 'SET_UPLOAD_ID':
      return { ...state, uploadId: action.payload };
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [
          ...state.messages,
          {
            ...action.payload,
            id: Date.now().toString(),
            timestamp: new Date(),
          },
        ],
      };
    case 'SET_PROCESSING':
      return { ...state, isProcessing: action.payload };
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] };
    default:
      return state;
  }
}

const initialState: State = {
  appState: 'upload',
  uploadId: null,
  messages: [],
  isProcessing: false,
};

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const contextValue: AppContextType = {
    state: state.appState,
    uploadId: state.uploadId,
    messages: state.messages,
    isProcessing: state.isProcessing,
    setState: (newState) => dispatch({ type: 'SET_STATE', payload: newState }),
    setUploadId: (id) => dispatch({ type: 'SET_UPLOAD_ID', payload: id }),
    addMessage: (message) => dispatch({ type: 'ADD_MESSAGE', payload: message }),
    setProcessing: (processing) => dispatch({ type: 'SET_PROCESSING', payload: processing }),
    clearMessages: () => dispatch({ type: 'CLEAR_MESSAGES' }),
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
