import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Paper, Typography } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { documentApi } from '../services/api';
import { useAppStore } from '../store/appStore';

export default function DocumentUpload() {
  const { setCurrentDocument, setLoading, setError } = useAppStore();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    try {
      setLoading(true);
      setError(null);
      const file = acceptedFiles[0];
      const document = await documentApi.upload(file);
      setCurrentDocument(document);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  }, [setCurrentDocument, setLoading, setError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: false,
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 3,
        textAlign: 'center',
        cursor: 'pointer',
        bgcolor: isDragActive ? 'action.hover' : 'background.paper',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'divider',
      }}
    >
      <input {...getInputProps()} />
      <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
      <Typography variant="h6" gutterBottom>
        {isDragActive ? 'Drop the file here' : 'Drag and drop a document here'}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        or click to select a file
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
        Supported formats: PDF, DOC, DOCX
      </Typography>
    </Paper>
  );
} 