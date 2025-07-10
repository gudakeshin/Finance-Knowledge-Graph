import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert, Card, CardContent, Grid } from '@mui/material';
import { graphApi } from '../services/api';

interface SimpleGraphViewProps {
  documentId: string;
}

interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: string;
    properties: Record<string, any>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
    properties: Record<string, any>;
  }>;
  metadata: {
    document_id: string;
    total_nodes: number;
    total_edges: number;
    generated_at: string;
  };
}

export default function SimpleGraphView({ documentId }: SimpleGraphViewProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (documentId) {
      loadGraphData();
    }
  }, [documentId]);

  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await graphApi.getGraph(documentId, {
        include_entities: true,
        include_relationships: true,
        max_nodes: 50
      });
      
      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!graphData) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary">
          No graph data available
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload and process a document to see the knowledge graph
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: '600px', overflow: 'auto' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Knowledge Graph Data
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Document: {documentId} | Nodes: {graphData.metadata.total_nodes} | 
          Edges: {graphData.metadata.total_edges}
        </Typography>
      </Box>
      
      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>
            Nodes ({graphData.nodes.length})
          </Typography>
          {graphData.nodes.map((node) => (
            <Card key={node.id} sx={{ mb: 1, backgroundColor: '#e3f2fd' }}>
              <CardContent sx={{ py: 1, px: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  {node.label}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Type: {node.type} | ID: {node.id}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>
            Relationships ({graphData.edges.length})
          </Typography>
          {graphData.edges.map((edge) => (
            <Card key={edge.id} sx={{ mb: 1, backgroundColor: '#f3e5f5' }}>
              <CardContent sx={{ py: 1, px: 2 }}>
                <Typography variant="subtitle2" fontWeight="bold">
                  {edge.type}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {edge.source} → {edge.target}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Grid>
      </Grid>
    </Paper>
  );
} 