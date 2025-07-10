import { useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
} from '@mui/material';
import { documentApi } from '../services/api';
import { useAppStore } from '../store/appStore';

export default function ValidationResults() {
  const { currentDocument, validationResults, setValidationResults, setLoading, setError } = useAppStore();

  useEffect(() => {
    const validateDocument = async () => {
      if (!currentDocument) return;

      try {
        setLoading(true);
        setError(null);
        const results = await documentApi.validate(currentDocument.id);
        setValidationResults(results);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Failed to validate document');
      } finally {
        setLoading(false);
      }
    };

    validateDocument();
  }, [currentDocument, setValidationResults, setLoading, setError]);

  if (!currentDocument) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PASS':
        return 'success';
      case 'FAIL':
        return 'error';
      case 'WARNING':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Validation Results
      </Typography>
      {validationResults.length === 0 ? (
        <Typography color="text.secondary">No validation results available</Typography>
      ) : (
        <List>
          {validationResults.map((result) => (
            <ListItem key={result.id}>
              <Card sx={{ width: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Chip
                      label={result.properties.status}
                      color={getStatusColor(result.properties.status)}
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <Typography variant="subtitle1">
                      {result.properties.message}
                    </Typography>
                  </Box>
                  {result.properties.details && (
                    <Typography variant="body2" color="text.secondary">
                      {JSON.stringify(result.properties.details, null, 2)}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </ListItem>
          ))}
        </List>
      )}
    </Box>
  );
} 