import React, { useState, useCallback } from 'react';
import { Upload, FileText, Download, Eye, Trash2, CheckCircle, AlertCircle, FileType, Target } from 'lucide-react';
import { extractionApi } from '../services/api';
import type { ExtractionResultType, DocumentClassification } from '../services/api';

const DocumentExtraction: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractionResults, setExtractionResults] = useState<ExtractionResultType[]>([]);
  const [documentClassification, setDocumentClassification] = useState<DocumentClassification | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [error, setError] = useState<string>('');

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) {
      handleFileSelect(droppedFiles[0]);
    }
  }, []);

  const handleFileSelect = (selectedFile: File) => {
    if (selectedFile.type.startsWith('image/') || selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError('');
      
      // Create preview URL
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
      
      // Clear previous results
      setExtractionResults([]);
      setDocumentClassification(null);
    } else {
      setError('Please select an image file (PNG, JPG, JPEG) or PDF file.');
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleExtract = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError('');
    
    try {
      console.log('Starting extraction for file:', file.name, file.size, file.type);
      
      // Use the real API
      const response = await extractionApi.extract(file);
      console.log('API extraction response:', response);
      setExtractionResults(response.extraction_results);
      setDocumentClassification(response.document_classification);
    } catch (error: any) {
      console.error('Extraction failed:', error);
      setError(error.response?.data?.detail || error.message || 'Extraction failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setExtractionResults([]);
    setDocumentClassification(null);
    setError('');
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl('');
    }
  };

  const downloadResults = () => {
    if (extractionResults.length === 0) return;

    const csvContent = [
      'Field,Value,Confidence,Entity Type',
      ...extractionResults.map(result => 
        `"${result.field}","${result.value}",${result.confidence},"${result.entity_type || ''}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'extraction_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Document Extraction
          </h1>
          <p className="text-lg text-gray-600">
            Upload documents and extract structured data with AI
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* Top Row: Upload Document and Document Preview side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Upload Document Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Upload Document
            </h2>
            
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isDragging
                  ? 'border-blue-400 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {!file ? (
                <div className="space-y-3">
                  <Upload className="mx-auto h-8 w-8 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Drop your document here or click to browse
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Supports PDF, PNG, JPG, JPEG files
                    </p>
                  </div>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileInput}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors text-sm"
                  >
                    Choose File
                  </label>
                </div>
              ) : (
                <div className="space-y-3">
                  <FileText className="mx-auto h-8 w-8 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleExtract}
                      disabled={isProcessing}
                      className="inline-flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                    >
                      {isProcessing ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3 mr-2" />
                          Extract Data
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleClear}
                      className="inline-flex items-center px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm"
                    >
                      <Trash2 className="h-3 w-3 mr-2" />
                      Clear
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Document Preview Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Document Preview
            </h2>
            {previewUrl ? (
              <div className="border rounded-lg overflow-hidden">
                {file?.type.startsWith('image/') ? (
                  <img
                    src={previewUrl}
                    alt="Document preview"
                    className="w-full h-auto max-h-96 object-contain"
                  />
                ) : (
                  <iframe
                    src={previewUrl}
                    title="PDF Preview"
                    className="w-full h-96 border rounded"
                  />
                )}
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500">No document selected</p>
                <p className="text-sm text-gray-400">Upload a document to see preview</p>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Row: Extraction Results and Document Classification side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Extraction Results Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Extraction Results
              </h2>
              {extractionResults.length > 0 && (
                <button
                  onClick={downloadResults}
                  className="inline-flex items-center px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                >
                  <Download className="h-4 w-4 mr-1" />
                  Export CSV
                </button>
              )}
            </div>

            {extractionResults.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <FileText className="mx-auto h-12 w-12 mb-4" />
                <p>No extraction results yet</p>
                <p className="text-sm">Upload a document and click "Extract Data" to get started</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {extractionResults.map((result, index) => (
                  <div
                    key={index}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-medium text-gray-900">
                            {result.field}
                          </h3>
                          {result.schema_field && (
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              Schema: {result.schema_field}
                            </span>
                          )}
                          {result.required && (
                            <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                              Required
                            </span>
                          )}
                        </div>
                        {result.entity_type === 'TEXT_PREVIEW' ? (
                          <div className="mt-2">
                            <p className="text-gray-700 whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border">
                              {result.value}
                            </p>
                          </div>
                        ) : (
                          <>
                            <p className="text-gray-700">{result.value}</p>
                            {result.entity_type && (
                              <p className="text-xs text-gray-500 mt-1">
                                Type: {result.entity_type}
                              </p>
                            )}
                          </>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center">
                          {result.confidence >= 0.8 ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertCircle className="h-4 w-4 text-yellow-500" />
                          )}
                          <span className="text-sm text-gray-500 ml-1">
                            {Math.round(result.confidence * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                    {result.bounding_box && (
                      <div className="mt-2 text-xs text-gray-500">
                        Position: ({result.bounding_box.x}, {result.bounding_box.y})
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Statistics */}
            {extractionResults.length > 0 && (
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Extraction Statistics
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {extractionResults.length}
                    </p>
                    <p className="text-sm text-gray-600">Fields Extracted</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {Math.round(
                        (extractionResults.filter(r => r.confidence >= 0.8).length /
                          extractionResults.length) *
                          100
                      )}%
                    </p>
                    <p className="text-sm text-gray-600">High Confidence</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Document Classification Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-4">
              <FileType className="h-5 w-5 text-blue-600 mr-2" />
              <h2 className="text-xl font-semibold text-gray-900">
                Document Classification
              </h2>
            </div>
            
            {documentClassification ? (
              <div className="space-y-4">
                {/* Classification Details */}
                <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg font-bold text-gray-900">
                        {documentClassification.type === 'custom' 
                          ? documentClassification.custom_type_name || 'Custom Document'
                          : documentClassification.type.replace('_', ' ').toUpperCase()
                        }
                      </span>
                      {documentClassification.type === 'custom' && (
                        <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                          Dynamic Type
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-2">
                      {documentClassification.suggested_schema.description}
                    </p>
                    {documentClassification.reasoning && (
                      <p className="text-xs text-gray-500 italic">
                        "{documentClassification.reasoning}"
                      </p>
                    )}
                  </div>
                  <div className="flex items-center">
                    <Target className="h-4 w-4 text-blue-600 mr-1" />
                    <span className="text-sm font-medium text-blue-600">
                      {Math.round(documentClassification.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>
                
                {/* Schema Information */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3 flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    Dynamic Schema: {documentClassification.suggested_schema.name}
                  </h3>
                  <p className="text-sm text-gray-600 mb-3">
                    {documentClassification.suggested_schema.description}
                  </p>
                  
                  {/* Schema Fields */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-gray-700">Extractable Fields:</h4>
                    <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                      {documentClassification.suggested_schema.fields.map((field, index) => (
                        <div
                          key={index}
                          className={`p-3 rounded-lg border ${
                            field.required 
                              ? 'bg-red-50 border-red-200' 
                              : 'bg-white border-gray-200'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-gray-900">{field.name}</span>
                                <span className="text-xs text-gray-500">({field.key})</span>
                                {field.required && (
                                  <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                                    Required
                                  </span>
                                )}
                              </div>
                              {field.description && (
                                <p className="text-xs text-gray-600 mb-1">{field.description}</p>
                              )}
                              {field.examples && field.examples.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                  {field.examples.slice(0, 3).map((example, idx) => (
                                    <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                      {example}
                                    </span>
                                  ))}
                                  {field.examples.length > 3 && (
                                    <span className="text-xs text-gray-500">+{field.examples.length - 3} more</span>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <FileType className="mx-auto h-12 w-12 mb-4" />
                <p>No classification yet</p>
                <p className="text-sm">Upload and extract a document to see classification</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentExtraction; 