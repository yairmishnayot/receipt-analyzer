import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { processReceipt } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorDisplay from './ErrorDisplay';
import '../styles/ReceiptForm.css';

const ReceiptForm = () => {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [duplicateWarning, setDuplicateWarning] = useState(null);

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

    // Reset states
    setError(null);
    setSuccess(false);
    setDuplicateWarning(null);

    // Validate URL
    if (!url.trim()) {
      setError(t('form.urlRequired'));
      return;
    }

    if (!validateUrl(url)) {
      setError(t('form.urlError'));
      return;
    }

    // Process receipt
    setLoading(true);

    try {
      const result = await processReceipt(url, forceUpdate);

      if (result.success) {
        setSuccess(true);
        setUrl(''); // Clear form
        // Auto-dismiss success after 5 seconds
        setTimeout(() => setSuccess(false), 5000);
      } else if (result.is_duplicate) {
        // Show duplicate warning
        setDuplicateWarning({
          message: result.message,
          data: result.data,
          duplicateInfo: result.duplicate_info
        });
      } else {
        setError(result.error || result.message);
      }
    } catch (err) {
      setError(t('messages.errorGeneric'));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmUpdate = async () => {
    setDuplicateWarning(null);
    // Re-submit with force_update=true
    const fakeEvent = { preventDefault: () => {} };
    await handleSubmit(fakeEvent, true);
  };

  const handleCancelUpdate = () => {
    setDuplicateWarning(null);
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

        {loading && <LoadingSpinner />}

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
            {duplicateWarning.duplicateInfo && (
              <div className="duplicate-details">
                <p>שורת סיכום: {duplicateWarning.duplicateInfo.summary_row}</p>
                <p>מספר פריטים: {duplicateWarning.duplicateInfo.item_rows?.length || 0}</p>
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
