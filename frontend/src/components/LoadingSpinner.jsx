import { useTranslation } from 'react-i18next';
import '../styles/LoadingSpinner.css';

const LoadingSpinner = () => {
  const { t } = useTranslation();

  return (
    <div className="loading-spinner-container">
      <div className="spinner"></div>
      <p className="loading-text">{t('form.processing')}</p>
    </div>
  );
};

export default LoadingSpinner;
