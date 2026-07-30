import React from 'react';

interface Props {
  message: string;
}

export const UndevelopedBar: React.FC<Props> = ({ message }) => (
  <div className="undeveloped-bar">
    <span>⚠️</span>
    <span>{message}</span>
  </div>
);
