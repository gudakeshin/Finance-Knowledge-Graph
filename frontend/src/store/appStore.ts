import { create } from 'zustand';
import type { Document, ValidationResult, Correction } from '../types/entities';

interface AppState {
  currentDocument: Document | null;
  validationResults: ValidationResult[];
  corrections: Correction[];
  isLoading: boolean;
  error: string | null;
  setCurrentDocument: (document: Document | null) => void;
  setValidationResults: (results: ValidationResult[]) => void;
  setCorrections: (corrections: Correction[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentDocument: null,
  validationResults: [],
  corrections: [],
  isLoading: false,
  error: null,
  setCurrentDocument: (document) => set({ currentDocument: document }),
  setValidationResults: (results) => set({ validationResults: results }),
  setCorrections: (corrections) => set({ corrections }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
})); 