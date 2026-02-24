import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import useReceiptStream from '../hooks/useReceiptStream';
import ProcessingProgress from './ProcessingProgress';
import ErrorDisplay from './ErrorDisplay';
import '../styles/ReceiptForm.css';

const ReceiptForm = () => {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [error, setError] = useState(null);
  const {
    loading,
    progress,
    currentStep,
    success,
    duplicateWarning,
    processReceipt,
    reset,
  } = useReceiptStream();

  useEffect(() => {
    if (success) {
      setUrl('');
      const timer = setTimeout(() => reset(), 5000);
      return () => clearTimeout(timer);
    }
  }, [success, reset]);

  const validateUrl = (urlString) => {
    try {
      new URL(urlString);
      return true;
    } catch {
      return false;
    }
  };

  const handleSubmit = async (e, forceUpdate = false) => {
    e.preventDefault();

    reset();
    setError(null);

    if (!url.trim()) {
      setError(t('form.urlRequired'));
      return;
    }

    if (!validateUrl(url)) {
      setError(t('form.urlError'));
      return;
    }

    await processReceipt(url, forceUpdate);
  };

  const handleConfirmUpdate = async () => {
    setDuplicateWarning(null);
    const fakeEvent = { preventDefault: () => {} };
    await handleSubmit(fakeEvent, true);
  };

  const handleCancelUpdate = () => {
    setDuplicateWarning(null);
    reset();
  };

  const handleDismissError = () => {
    setError(null);
  };

  return (
    <div className="receipt-form-container">
      <div className="receipt-form-card">
        <h1 className="form-title">{t('app.title')}</h1>
        <p className="form-subtitle">{t('app.subtitle')}</p>

        <form onSubmit={handleSubmit} className="receipt-form">
          <div className="form-group">
            <label htmlFor="receipt-url" className="form-label">
              {t('form.urlLabel')}
            </label>
            <input
              id="receipt-url"
              type="text"
              className="form-input"
              placeholder={t('form.urlPlaceholder')}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={loading}
              dir="ltr"
            />
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={loading || !url.trim()}
          >
            {loading ? t('form.processing') : t('form.submitButton')}
          </button>
        </form>

        {loading && (
          <ProcessingProgress currentStep={currentStep} progress={progress} />
        )}

        {error && <ErrorDisplay error={error} onDismiss={handleDismissError} />}

        {success && (
          <div className="success-message">
            <span className="success-icon">✓</span>
            <div>
              <strong>{t('messages.success')}</strong>
              <p>{t('messages.successDetails')}</p>
            </div>
          </div>
        )}

        {duplicateWarning && (
          <div className="duplicate-warning">
            <div className="warning-header">
              <span className="warning-icon">⚠️</span>
              <strong>קבלה כפולה</strong>
            </div>
            <p className="warning-message">{duplicateWarning.message}</p>
            {duplicateWarning.duplicate_info && (
              <div className="duplicate-details">
                <p>שורת סיכום: {duplicateWarning.duplicate_info.summary_row}</p>
                <p>מספר פריטים: {duplicateWarning.duplicate_info.item_rows?.length || 0}</p>
              </div>
            )}
            <div className="warning-actions">
              <button
                onClick={handleConfirmUpdate}
                className="confirm-button"
              >
                ✓ עדכן קבלה
              </button>
              <button
                onClick={handleCancelUpdate}
                className="cancel-button"
              >
                ✗ בטל
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptForm;
