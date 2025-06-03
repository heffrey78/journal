import React from 'react';
import Link from 'next/link';

const Logo: React.FC = () => {
  return (
    <Link href="/" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
      <img
        src="/llens.png"
        alt="Llens"
        className="h-12 w-auto"
      />
      <span className="text-2xl font-bold text-primary">
        Llens
      </span>
    </Link>
  );
};

export default Logo;
