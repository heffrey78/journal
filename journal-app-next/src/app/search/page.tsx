'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Preserve any existing search parameters and redirect to entries page
    const params = new URLSearchParams(searchParams.toString());
    const queryString = params.toString();
    const newUrl = queryString ? `/entries?${queryString}` : '/entries';

    // Use replace to avoid adding this redirect to browser history
    router.replace(newUrl);
  }, [router, searchParams]);

  // Show a loading spinner while redirecting
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Redirecting to search...</p>
      </div>
    </div>
  );
}
