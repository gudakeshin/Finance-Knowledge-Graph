export enum EntityType {
  DOCUMENT = "Document",
  SECTION = "Section",
  PARAGRAPH = "Paragraph",
  SENTENCE = "Sentence",
  ENTITY = "Entity",
  RELATIONSHIP = "Relationship",
  VALIDATION_RULE = "ValidationRule",
  VALIDATION_RESULT = "ValidationResult",
  CORRECTION = "Correction",
  USER = "User",
  ORGANIZATION = "Organization",
  PROJECT = "Project",
  WORKSPACE = "Workspace",
  TAG = "Tag",
  COMMENT = "Comment",
  VERSION = "Version",
  AUDIT_LOG = "AuditLog",
  SYSTEM = "System",
  FUND = "Fund",
  COMPLIANCE_CHECK = "ComplianceCheck"
}

export interface Entity {
  id: string;
  type: EntityType;
  properties: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface Document extends Entity {
  type: EntityType.DOCUMENT;
  properties: {
    title: string;
    content: string;
    format: string;
    size: number;
    metadata: Record<string, any>;
  };
}

export interface ValidationResult extends Entity {
  type: EntityType.VALIDATION_RESULT;
  properties: {
    ruleId: string;
    status: 'PASS' | 'FAIL' | 'WARNING';
    message: string;
    details: Record<string, any>;
  };
}

export interface Correction extends Entity {
  type: EntityType.CORRECTION;
  properties: {
    strategy: string;
    status: 'PENDING' | 'APPLIED' | 'REJECTED';
    changes: Record<string, any>;
    appliedBy?: string;
    appliedAt?: string;
  };
}

export type { Document, ValidationResult, Correction }; 