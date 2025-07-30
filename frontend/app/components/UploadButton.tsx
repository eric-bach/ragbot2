'use client';

import { useRef, useState, useEffect } from 'react';
import { Upload, CheckCircle, XCircle, Loader2 } from 'lucide-react';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

export default function UploadButton() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [currentFileKey, setCurrentFileKey] = useState<string | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const startProcessing = (fileKey: string) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Wait 10 seconds then show success
    pollingIntervalRef.current = setTimeout(() => {
      setUploadStatus('success');
      pollingIntervalRef.current = null;

      // Reset after showing success for 3 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setSelectedFile(null);
        setCurrentFileKey(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 3000);
    }, 10000);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check if file is a PDF
      if (!file.type.includes('pdf')) {
        setErrorMessage('Please select a PDF file');
        setUploadStatus('error');
        return;
      }

      // Check file size (limit to 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setErrorMessage('File size must be less than 10MB');
        setUploadStatus('error');
        return;
      }

      setSelectedFile(file);
      setErrorMessage('');
      console.log('Selected file:', file.name);

      // Start upload immediately
      handleUpload(file);
    }
  };

  const handleUpload = async (file: File) => {
    setUploadStatus('uploading');
    setErrorMessage('');

    try {
      // Step 1: Get presigned URL
      console.log('Getting presigned URL for:', file.name);
      const presignedResponse = await fetch(`/api/presigned-url?file_name=${encodeURIComponent(file.name)}`);

      if (!presignedResponse.ok) {
        const errorData = await presignedResponse.json();
        throw new Error(errorData.details || `Failed to get presigned URL (${presignedResponse.status})`);
      }

      const presignedData = await presignedResponse.json();
      console.log('Presigned URL received:', { key: presignedData.key, bucket: presignedData.bucket });

      // Step 2: Upload file to S3 using presigned URL
      console.log('Uploading file to S3...');
      const uploadResponse = await fetch(presignedData.presignedurl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': 'application/pdf',
        },
      });

      if (!uploadResponse.ok) {
        throw new Error(`Failed to upload file to S3 (${uploadResponse.status})`);
      }

      console.log('File uploaded successfully');

      // Step 3: Set to processing state and start processing
      setUploadStatus('processing');
      setCurrentFileKey(presignedData.key);
      startProcessing(presignedData.key);
    } catch (error) {
      console.error('Upload error:', error);
      setErrorMessage(error instanceof Error ? error.message : 'Upload failed');
      setUploadStatus('error');

      // Reset error after 5 seconds
      setTimeout(() => {
        setUploadStatus('idle');
        setErrorMessage('');
        setCurrentFileKey(null);
      }, 5000);
    }
  };

  const getButtonContent = () => {
    switch (uploadStatus) {
      case 'uploading':
        return (
          <>
            <Loader2 size={14} className='animate-spin' />
            <span className='text-xs'>Uploading...</span>
          </>
        );
      case 'processing':
        return (
          <>
            <Loader2 size={14} className='animate-spin text-blue-500' />
            <span className='text-xs text-blue-500'>Processing...</span>
          </>
        );
      case 'success':
        return (
          <>
            <CheckCircle size={14} className='text-green-500' />
            <span className='text-xs text-green-500'>Success!</span>
          </>
        );
      case 'error':
        return (
          <>
            <XCircle size={14} className='text-red-500' />
            <span className='text-xs text-red-500'>Error</span>
          </>
        );
      default:
        return (
          <>
            <Upload size={14} />
            <span className='text-xs'>Upload</span>
          </>
        );
    }
  };

  const getButtonClass = () => {
    const baseClass = 'flex items-center space-x-1 transition-colors';

    switch (uploadStatus) {
      case 'uploading':
        return `${baseClass} text-blue-500 cursor-not-allowed`;
      case 'processing':
        return `${baseClass} text-blue-500 cursor-not-allowed`;
      case 'success':
        return `${baseClass} text-green-500 cursor-not-allowed`;
      case 'error':
        return `${baseClass} text-red-500 cursor-not-allowed`;
      default:
        return `${baseClass} text-muted-foreground hover:text-foreground cursor-pointer`;
    }
  };

  return (
    <div className='relative'>
      <button
        type='button'
        onClick={uploadStatus === 'idle' ? handleUploadClick : undefined}
        className={getButtonClass()}
        title={uploadStatus === 'idle' ? 'Upload Document' : uploadStatus}
        disabled={uploadStatus !== 'idle'}
      >
        {getButtonContent()}
      </button>

      {errorMessage && (
        <div className='absolute top-full left-0 mt-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded shadow-lg z-10 max-w-xs'>
          {errorMessage}
        </div>
      )}

      <input ref={fileInputRef} type='file' onChange={handleFileChange} className='hidden' accept='.pdf' />
    </div>
  );
}
