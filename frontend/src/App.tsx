import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ValidationResults from './components/ValidationResults';
import GraphVisualization from './components/GraphVisualization';
import SimpleGraphView from './components/SimpleGraphView';
import DocumentExtraction from './components/DocumentExtraction';
import BackendLogs from './components/BackendLogs';
import { useAppStore } from './store/appStore';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [useSimpleGraph, setUseSimpleGraph] = useState(false);
  const { currentDocument } = useAppStore();

  const handleGraphError = () => {
    setUseSimpleGraph(true);
  };

  const tabs = [
    { name: 'Document Upload', component: <DocumentUpload /> },
    { name: 'Document Extraction', component: <DocumentExtraction /> },
    { name: 'Validation Results', component: <ValidationResults /> },
    { 
      name: 'Knowledge Graph', 
      component: currentDocument ? (
        useSimpleGraph ? (
          <SimpleGraphView documentId={currentDocument.id} />
        ) : (
          <GraphVisualization 
            documentId={currentDocument.id} 
            onError={handleGraphError}
          />
        )
      ) : (
        <div className="text-center p-8">
          <h3 className="text-xl font-semibold text-gray-600 mb-2">
            No document selected
          </h3>
          <p className="text-gray-500">
            Please upload a document first to view the knowledge graph
          </p>
        </div>
      )
    },
    { name: 'Backend Logs', component: <BackendLogs /> }
  ];

  return (
    <div className="min-h-screen bg-gray-50 w-full">
      <div className="w-full px-2 sm:px-6 lg:px-12 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Finance Knowledge Graph
          </h1>
          <p className="text-xl text-gray-600">
            Document Processing & Validation System
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden w-full">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab, index) => (
                <button
                  key={index}
                  onClick={() => setActiveTab(index)}
                  className={`
                    py-4 px-1 border-b-2 font-medium text-sm
                    ${activeTab === index
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content: Render all, hide inactive with CSS */}
          <div className="p-6 w-full">
            {tabs.map((tab, idx) => (
              <div key={idx} style={{ display: activeTab === idx ? 'block' : 'none', width: '100%' }}>
                {tab.component}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
