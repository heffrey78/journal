'use client';

import React from 'react';
import MainLayout from '@/components/layout/MainLayout';
import { cn } from '@/lib/utils';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <MainLayout>
      <div className={cn(
        'h-full w-full',
        'flex flex-col',
        'px-4 py-6'
      )}>
        {children}
      </div>
    </MainLayout>
  );
}
