// Core Design System Components
// Re-export UI components with a unified interface

// Button components
export { Button, buttonVariants } from '@/components/ui/button';
export type { ButtonProps } from '@/components/ui/button';

// Card components
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card';

// Form components
export { Input } from '@/components/ui/input';
export { Button as FormButton } from '@/components/ui/button';

// Feedback components
export { Alert } from '@/components/ui/alert';
export { Badge } from '@/components/ui/badge';
export { Skeleton } from '@/components/ui/skeleton';

// Navigation components
export { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Dialog components
export {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

// Utility components
export { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
export { Collapsible, CollapsibleSection } from '@/components/ui/collapsible';

// Navigation components
export { Pagination } from './Pagination';

// Layout components
export { default as Container } from '@/components/layout/Container';
export { default as ContentPadding } from '@/components/layout/ContentPadding';
export { default as Stack } from '@/components/layout/Stack';
export { default as Cluster } from '@/components/layout/Cluster';
export { default as Grid } from '@/components/layout/Grid';
export { default as CardGrid } from '@/components/layout/CardGrid';
export { default as CardList } from '@/components/layout/CardList';
