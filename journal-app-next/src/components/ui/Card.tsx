import React from 'react';
import { Card as ShadcnCard } from './card';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  clickable?: boolean;
}

/**
 * @deprecated Use the shadcn Card component from './card.tsx' instead
 */
const Card: React.FC<CardProps> = ({ children, className = '', clickable = false }) => {
  // Create a combined className that includes hover effects if clickable
  const combinedClassName = `${clickable ? 'cursor-pointer hover:shadow-md' : ''} p-6 ${className}`;

  return (
    <ShadcnCard className={combinedClassName}>
      {children}
    </ShadcnCard>
  );
};

export default Card;
