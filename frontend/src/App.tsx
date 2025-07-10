import React, { useState } from 'react';
import { Container, Box, Typography, Tabs, Tab, Paper } from '@mui/material';
import DocumentUpload from './components/DocumentUpload';
import ValidationResults from './components/ValidationResults';
import GraphVisualization from './components/GraphVisualization';
import SimpleGraphView from './components/SimpleGraphView';
import { useAppStore } from './store/appStore';
import './App.css';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [useSimpleGraph, setUseSimpleGraph] = useState(false);
  const { currentDocument } = useAppStore();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleGraphError = () => {
    setUseSimpleGraph(true);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          Finance Knowledge Graph
        </Typography>
        <Typography variant="h6" component="h2" gutterBottom align="center" color="text.secondary">
          Document Processing & Validation System
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="Finance Knowledge Graph tabs">
            <Tab label="Document Upload" />
            <Tab label="Validation Results" />
            <Tab label="Knowledge Graph" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <DocumentUpload />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <ValidationResults />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          {currentDocument ? (
            useSimpleGraph ? (
              <SimpleGraphView documentId={currentDocument.id} />
            ) : (
              <GraphVisualization 
                documentId={currentDocument.id} 
                onError={handleGraphError}
              />
            )
          ) : (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                No document selected
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Please upload a document first to view the knowledge graph
              </Typography>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
}

export default App;
