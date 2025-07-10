import React, { useState, useEffect } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges
} from 'reactflow';
import type { Node, Edge, NodeChange, EdgeChange } from 'reactflow';
import 'reactflow/dist/style.css';
import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { graphApi } from '../services/api';

interface GraphVisualizationProps {
  documentId: string;
  onError?: () => void;
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

const nodeTypes = {
  entity: ({ data }: { data: any }) => (
    <div style={{
      padding: '10px',
      borderRadius: '8px',
      backgroundColor: '#e3f2fd',
      border: '2px solid #2196f3',
      minWidth: '120px',
      textAlign: 'center'
    }}>
      <div style={{ fontWeight: 'bold', fontSize: '12px' }}>{data.label}</div>
      <div style={{ fontSize: '10px', color: '#666' }}>{data.type}</div>
    </div>
  ),
  relationship: ({ data }: { data: any }) => (
    <div style={{
      padding: '8px',
      borderRadius: '6px',
      backgroundColor: '#f3e5f5',
      border: '2px solid #9c27b0',
      minWidth: '100px',
      textAlign: 'center'
    }}>
      <div style={{ fontWeight: 'bold', fontSize: '11px' }}>{data.label}</div>
      <div style={{ fontSize: '9px', color: '#666' }}>{data.type}</div>
    </div>
  )
};

export default function GraphVisualization({ documentId, onError }: GraphVisualizationProps) {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

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
      
      // Convert to ReactFlow format
      const flowNodes: Node[] = data.nodes.map((node: any, index: number) => ({
        id: node.id,
        type: node.type === 'ENTITY' ? 'entity' : 'relationship',
        position: { 
          x: 100 + (index * 200), 
          y: 100 + (index % 3) * 150 
        },
        data: { 
          label: node.label, 
          type: node.type,
          properties: node.properties 
        }
      }));
      
      const flowEdges: Edge[] = data.edges.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.type,
        type: 'smoothstep',
        style: { stroke: '#666', strokeWidth: 2 }
      }));
      
      setNodes(flowNodes);
      setEdges(flowEdges);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load graph data';
      setError(errorMessage);
      if (onError) {
        onError();
      }
    } finally {
      setLoading(false);
    }
  };

  const onNodesChange = (changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  };

  const onEdgesChange = (changes: EdgeChange[]) => {
    setEdges((eds) => applyEdgeChanges(changes, eds));
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
    <Paper sx={{ p: 2, height: '600px' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Knowledge Graph Visualization
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Document: {documentId} | Nodes: {graphData.metadata.total_nodes} | 
          Edges: {graphData.metadata.total_edges}
        </Typography>
      </Box>
      
      <Box sx={{ height: '500px', border: '1px solid #ddd', borderRadius: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
        >
          <Controls />
          <Background />
          <MiniMap />
        </ReactFlow>
      </Box>
    </Paper>
  );
} 