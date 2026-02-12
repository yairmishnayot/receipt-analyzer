import { useTranslation } from 'react-i18next';
import '../styles/ErrorDisplay.css';

const ErrorDisplay = ({ error, onDismiss }) => {
  const { t } = useTranslation();

  if (!error) return null;

  return (
    <div className="error-display">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <div className="error-message">
          <strong>{t('messages.error')}</strong>
          <p>{error}</p>
        </div>
        {onDismiss && (
          <button className="error-dismiss" onClick={onDismiss} aria-label="Dismiss">
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default ErrorDisplay;
