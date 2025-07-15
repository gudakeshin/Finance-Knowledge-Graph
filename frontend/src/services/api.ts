import axios from 'axios';
import type { Document, ValidationResult, Correction } from '../types/entities';

const API_BASE_URL = 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Define the interface as a type export
export type ExtractionResultType = {
  field: string;
  key: string;
  value: string;
  confidence: number;
  entity_type?: string;
  schema_field?: string;
  required?: boolean;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
};

export interface DocumentClassification {
  type: string;
  confidence: number;
  custom_type_name?: string;
  reasoning?: string;
  suggested_schema: {
    name: string;
    description: string;
    fields: Array<{
      name: string;
      key: string;
      required: boolean;
      description?: string;
      examples?: string[];
    }>;
  };
}

export interface ExtractionResponse {
  success: boolean;
  file_id: string;
  filename: string;
  document_classification: DocumentClassification;
  extraction_results: ExtractionResultType[];
  total_fields: number;
  high_confidence_count: number;
}

export const extractionApi = {
  extract: async (file: File): Promise<ExtractionResponse> => {
    console.log('API: Starting extraction for file:', file.name, file.size, file.type);
    
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('API: Sending request to /api/v1/extraction/extract');
    const response = await api.post('/api/v1/extraction/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    console.log('API: Received response:', response.data);
    return response.data;
  },

  getFields: async () => {
    const response = await api.get('/api/v1/extraction/fields');
    return response.data.fields;
  },

  getStatus: async (fileId: string) => {
    const response = await api.get(`/api/v1/extraction/status/${fileId}`);
    return response.data;
  },
};

export const documentApi = {
  upload: async (file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/v1/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    // Convert the upload response to match Document type
    const uploadResponse = response.data;
    return {
      id: uploadResponse.document_id,
      type: 'Document' as any,
      properties: {
        title: file.name,
        content: '',
        format: file.type,
        size: file.size,
        metadata: {
          status: uploadResponse.status,
          uploadedAt: new Date().toISOString()
        }
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  },

  validate: async (documentId: string, rules?: string[]): Promise<ValidationResult[]> => {
    const response = await api.post(`/api/v1/documents/${documentId}/validate`, {
      rules: rules
    });
    
    return response.data.validation_results.map((result: any) => ({
      id: result.id || `validation-${Date.now()}`,
      type: 'ValidationResult' as any,
      properties: {
        ruleId: result.rule_id || 'rule-1',
        status: result.status || 'PASS',
        message: result.message || 'Validation completed',
        details: result.details || {}
      },
      createdAt: result.created_at || new Date().toISOString(),
      updatedAt: result.updated_at || new Date().toISOString()
    }));
  },

  process: async (documentId: string, options?: {
    extract_entities?: boolean;
    extract_relationships?: boolean;
    build_graph?: boolean;
  }): Promise<any> => {
    const response = await api.post(`/api/v1/documents/${documentId}/process`, {
      document_id: documentId,
      extract_entities: options?.extract_entities ?? true,
      extract_relationships: options?.extract_relationships ?? true,
      build_graph: options?.build_graph ?? true
    });
    
    return response.data;
  },

  getCorrections: async (documentId: string): Promise<Correction[]> => {
    const response = await api.get(`/api/v1/documents/${documentId}/corrections`);
    return response.data.corrections.map((correction: any) => ({
      id: correction.id,
      type: 'Correction' as any,
      properties: {
        strategy: correction.strategy || 'placeholder',
        status: correction.status || 'PENDING',
        changes: correction.changes || {},
        appliedBy: correction.applied_by,
        appliedAt: correction.applied_at
      },
      createdAt: correction.created_at || new Date().toISOString(),
      updatedAt: correction.updated_at || new Date().toISOString()
    }));
  },

  applyCorrection: async (documentId: string, correctionId: string): Promise<Correction> => {
    const response = await api.post(`/api/v1/documents/${documentId}/corrections/${correctionId}/apply`);
    return {
      id: correctionId,
      type: 'Correction' as any,
      properties: {
        strategy: 'applied',
        status: 'APPLIED' as const,
        changes: response.data.result || {},
        appliedBy: 'system',
        appliedAt: new Date().toISOString()
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
  },

  createCorrection: async (documentId: string, validationResultId: string, strategy: string, description: string): Promise<any> => {
    const response = await api.post(`/api/v1/documents/${documentId}/corrections`, {
      document_id: documentId,
      validation_result_id: validationResultId,
      strategy: strategy,
      description: description
    });
    
    return response.data;
  },
};

export const graphApi = {
  getGraph: async (documentId: string, options?: {
    include_entities?: boolean;
    include_relationships?: boolean;
    max_nodes?: number;
  }) => {
    const params = new URLSearchParams();
    if (options?.include_entities !== undefined) params.append('include_entities', options.include_entities.toString());
    if (options?.include_relationships !== undefined) params.append('include_relationships', options.include_relationships.toString());
    if (options?.max_nodes) params.append('max_nodes', options.max_nodes.toString());
    
    const response = await api.get(`/api/v1/graph/${documentId}?${params.toString()}`);
    return response.data;
  },

  getNodeDetails: async (nodeId: string) => {
    const response = await api.get(`/api/v1/graph/nodes/${nodeId}`);
    return response.data;
  },

  getRelationships: async (nodeId: string) => {
    const response = await api.get(`/api/v1/graph/nodes/${nodeId}/relationships`);
    return response.data.relationships;
  },
};

export const validationApi = {
  getRules: async () => {
    const response = await api.get('/api/v1/validation/rules');
    return response.data.rules;
  },

  createRule: async (rule: any) => {
    const response = await api.post('/api/v1/validation/rules', rule);
    return response.data.rule;
  },

  updateRule: async (ruleId: string, rule: any) => {
    const response = await api.put(`/api/v1/validation/rules/${ruleId}`, rule);
    return response.data.rule;
  },

  deleteRule: async (ruleId: string) => {
    const response = await api.delete(`/api/v1/validation/rules/${ruleId}`);
    return response.data;
  },
}; 