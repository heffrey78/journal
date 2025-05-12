import React from 'react';

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <section className="w-full max-w-6xl mx-auto">
      {children}
    </section>
  );
}
