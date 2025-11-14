import React from 'react';
import WorkflowBuilder from './components/WorkflowBuilder/WorkflowBuilder';
import './App.css';

function App() {
  const handleSave = (data: any) => {
    console.log('Saving workflow:', data);
    // Implement your save logic here
  };

  const handleLoad = async () => {
    // Implement your load logic here
    return null;
  };

  return (
    <div className="App">
      <WorkflowBuilder
        onSave={handleSave}
        onLoad={handleLoad}
        apiBaseUrl="/api/v1"
      />
    </div>
  );
}

export default App;

