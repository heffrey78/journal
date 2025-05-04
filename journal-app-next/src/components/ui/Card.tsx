import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  clickable?: boolean;
}

const Card: React.FC<CardProps> = ({ children, className = '', clickable = false }) => {
  const baseStyles = 'bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700';
  const hoverStyles = clickable ? 'cursor-pointer hover:shadow-md transition-shadow' : '';

  return (
    <div className={`${baseStyles} ${hoverStyles} ${className}`}>
      {children}
    </div>
  );
};

export default Card;
