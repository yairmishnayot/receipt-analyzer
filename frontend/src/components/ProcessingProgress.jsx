import { useTranslation } from 'react-i18next';
import '../styles/ProcessingProgress.css';

const STEPS = [
  { key: 'scrape', order: 1 },
  { key: 'parse', order: 2 },
  { key: 'classify', order: 3 },
  { key: 'check_duplicate', order: 4 },
  { key: 'sheets', order: 5 },
];

const ProcessingProgress = ({ currentStep, progress }) => {
  const { t } = useTranslation();

  const getStepClass = (order) => {
    if (order < currentStep) return 'completed';
    if (order === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="processing-progress">
      <div className="progress-steps">
        {STEPS.map((step, index) => (
          <div key={step.key} className="progress-step-wrapper">
            <div className={`progress-step ${getStepClass(step.order)}`}>
              <div className="step-circle">
                {step.order < currentStep ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  <span>{step.order}</span>
                )}
              </div>
              <span className="step-label">{t(`form.steps.${step.key}`)}</span>
            </div>
            {index < STEPS.length - 1 && (
              <div className={`step-connector ${step.order < currentStep ? 'completed' : ''}`} />
            )}
          </div>
        ))}
      </div>
      {currentStep && (
        <p className="progress-message">{t(`form.steps.${currentStep}`)}</p>
      )}
      <div className="progress-bar-container">
        <div className="progress-bar" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
};

export default ProcessingProgress;
