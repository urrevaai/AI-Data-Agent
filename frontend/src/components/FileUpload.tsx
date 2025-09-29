import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUploadCloud, FiFile } from 'react-icons/fi';
import axios from 'axios';
import { useApp } from '../contexts/AppContext';

const FileUpload: React.FC = () => {
  const { setState, setUploadId } = useApp();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setState('loading');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.upload_id) {
        setUploadId(response.data.upload_id);
        setState('chat');
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setState('upload');
      // You could add error handling UI here
    }
  }, [setState, setUploadId]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    multiple: false,
  });

  const getBorderColor = () => {
    if (isDragReject) return 'border-red-500';
    if (isDragAccept) return 'border-primary-blue';
    if (isDragActive) return 'border-primary-blue';
    return 'border-dark-border';
  };

  const getBackgroundColor = () => {
    if (isDragActive) return 'bg-primary-blue/5';
    return 'bg-dark-card';
  };

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-primary-text mb-4">
            AI Data Agent
          </h1>
          <p className="text-xl text-primary-muted">
            Upload your Excel file to start analyzing your data with AI
          </p>
        </div>

        <div
          {...getRootProps()}
          className={`
            relative cursor-pointer transition-all duration-300 ease-in-out
            border-2 border-dashed rounded-2xl p-12
            ${getBorderColor()} ${getBackgroundColor()}
            hover:border-primary-blue hover:bg-primary-blue/5
            focus:outline-none focus:ring-2 focus:ring-primary-blue focus:ring-offset-2 focus:ring-offset-dark-bg
          `}
        >
          <input {...getInputProps()} />
          
          <div className="text-center">
            <div className="mb-6">
              {isDragActive ? (
                <FiFile className="w-16 h-16 mx-auto text-primary-blue animate-pulse" />
              ) : (
                <FiUploadCloud className="w-16 h-16 mx-auto text-primary-muted" />
              )}
            </div>

            <div className="mb-4">
              {isDragActive ? (
                <p className="text-xl font-medium text-primary-blue">
                  Drop your file here...
                </p>
              ) : (
                <p className="text-xl font-medium text-primary-text">
                  Drop your Excel file here, or click to select
                </p>
              )}
            </div>

            <p className="text-primary-muted mb-6">
              Supports .xlsx, .xls, and .csv files up to 10MB
            </p>

            <div className="inline-flex items-center px-6 py-3 bg-primary-blue text-white font-medium rounded-lg hover:bg-blue-600 transition-colors">
              <FiUploadCloud className="w-5 h-5 mr-2" />
              Choose File
            </div>
          </div>

          {isDragReject && (
            <div className="absolute inset-0 flex items-center justify-center bg-red-500/10 rounded-2xl">
              <p className="text-red-400 font-medium">
                Please upload a valid Excel or CSV file
              </p>
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <p className="text-sm text-primary-muted">
            Your data is processed securely and never stored permanently
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;