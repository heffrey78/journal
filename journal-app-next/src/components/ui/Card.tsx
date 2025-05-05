import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  // Update to use CSS theme variables instead of hardcoded Tailwind colors
  const baseStyles = 'bg-card text-card-foreground rounded-lg shadow-sm p-6 border border-border';

  return (
    <div className={`${baseStyles} ${className}`}>
      {children}
    </div>
  );
};

export default Card;
