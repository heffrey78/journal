/**
 * Router compatibility utilities for supporting both Pages Router and App Router
 * This helps with the transition between Next.js routing systems.
 */
import { useRouter as usePageRouter } from 'next/router';
import { useRouter as useAppRouter, usePathname, useSearchParams } from 'next/navigation';

/**
 * Unified router hook that works with both Pages Router and App Router
 * Falls back to Pages Router when App Router fails
 */
export function useCompatRouter() {
  let appRouter;
  let pagesRouter;

  try {
    // Try to use App Router first
    appRouter = useAppRouter();
  } catch (error) {
    // Fall back to Pages Router if App Router fails
    console.debug('App Router not available, falling back to Pages Router');
  }

  try {
    // Always try to get the Pages Router
    pagesRouter = usePageRouter();
  } catch (error) {
    // Pages Router not available
    console.debug('Pages Router not available');
  }

  // If App Router is available
  if (appRouter) {
    const pathname = usePathname();
    const searchParams = useSearchParams();

    // Create a unified router interface
    return {
      // Properties
      pathname,
      query: Object.fromEntries(searchParams || []),
      asPath: pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : ''),

      // Methods
      push: appRouter.push,
      replace: appRouter.replace,
      back: appRouter.back,
      prefetch: appRouter.prefetch,

      // Source identification
      _source: 'app-router'
    };
  }

  // Fall back to Pages Router
  if (pagesRouter) {
    return {
      ...pagesRouter,
      _source: 'pages-router'
    };
  }

  // Last resort fallback with minimal functionality
  return {
    pathname: typeof window !== 'undefined' ? window.location.pathname : '',
    query: {},
    asPath: typeof window !== 'undefined' ? window.location.pathname + window.location.search : '',
    push: (url: string) => {
      if (typeof window !== 'undefined') window.location.href = url;
      return Promise.resolve(true);
    },
    replace: (url: string) => {
      if (typeof window !== 'undefined') window.location.replace(url);
      return Promise.resolve(true);
    },
    back: () => {
      if (typeof window !== 'undefined') window.history.back();
    },
    prefetch: () => Promise.resolve(),
    _source: 'fallback'
  };
}
