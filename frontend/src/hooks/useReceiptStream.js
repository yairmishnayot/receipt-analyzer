import { useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const STEP_ORDER = {
  scrape: 1,
  parse: 2,
  classify: 3,
  check_duplicate: 4,
  sheets: 5,
};

export const useReceiptStream = () => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);
  const [result, setResult] = useState(null);

  const eventSourceRef = useRef(null);

  const reset = useCallback(() => {
    setLoading(false);
    setProgress(0);
    setCurrentStep(null);
    setError(null);
    setSuccess(false);
    setDuplicateWarning(null);
    setResult(null);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  const processReceipt = useCallback(async (url, forceUpdate = false) => {
    reset();
    setLoading(true);
    setProgress(0);
    setCurrentStep('scrape');

    const encodedUrl = encodeURIComponent(url);
    const eventSource = new EventSource(
      `${API_BASE_URL}/api/receipt/process/stream?url=${encodedUrl}&force_update=${forceUpdate}`
    );
    eventSourceRef.current = eventSource;

    return new Promise((resolve) => {
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'progress':
              setCurrentStep(data.step);
              setProgress(data.progress);
              break;

            case 'complete':
              setProgress(100);
              setCurrentStep('complete');
              setLoading(false);
              setSuccess(true);
              setResult({
                success: true,
                message: data.message,
                data: data.data,
                is_duplicate: data.is_duplicate,
              });
              eventSource.close();
              resolve({
                success: true,
                message: data.message,
                data: data.data,
                is_duplicate: data.is_duplicate,
              });
              break;

            case 'duplicate':
              setLoading(false);
              setDuplicateWarning({
                message: data.message,
                data: data.data,
                duplicate_info: data.duplicate_info,
              });
              eventSource.close();
              resolve({
                success: false,
                is_duplicate: true,
                message: data.message,
                data: data.data,
                duplicate_info: data.duplicate_info,
              });
              break;

            case 'error':
              setLoading(false);
              setError(data.message);
              eventSource.close();
              resolve({
                success: false,
                error: data.message,
              });
              break;
          }
        } catch (err) {
          console.error('Failed to parse SSE event:', err);
        }
      };

      eventSource.onerror = (err) => {
        console.error('SSE error:', err);
        setLoading(false);
        setError('Connection error');
        eventSource.close();
        resolve({
          success: false,
          error: 'Connection error',
        });
      };
    });
  }, [reset]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return {
    loading,
    progress,
    currentStep,
    error,
    success,
    duplicateWarning,
    result,
    processReceipt,
    reset,
  };
};

export default useReceiptStream;
