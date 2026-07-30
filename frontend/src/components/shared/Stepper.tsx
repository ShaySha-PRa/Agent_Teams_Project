import React from 'react';

interface Step {
  label: string;
  status: 'active' | 'inactive' | 'done' | 'completed' | string;
}

interface Props { steps: Step[]; }

export const Stepper: React.FC<Props> = ({ steps }) => (
  <div className="stepper">
    {steps.map((step, i) => (
      <React.Fragment key={i}>
        <div className="stepper-step">
          <div className={`stepper-circle ${step.status}`}>
            {step.status === 'done' ? '✓' : i + 1}
          </div>
          <span className={`stepper-label ${step.status}`}>{step.label}</span>
        </div>
        {i < steps.length - 1 && <div className="stepper-connector" />}
      </React.Fragment>
    ))}
  </div>
);
