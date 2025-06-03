/**
 * Layout component exports
 *
 * This file exports all layout components for easier importing throughout the application.
 * Import multiple components like:
 * import { Container, Stack, Grid } from '@/components/layout';
 */

// Core layout components
export { default as Container } from './Container';
export { default as ContentPadding } from './ContentPadding';
export { default as Stack } from './Stack';
export { default as Cluster } from './Cluster';
export { default as Grid } from './Grid';

// Higher-level layout components
export { default as SplitLayout } from './SplitLayout';
export { default as PageLayout } from './PageLayout';
export { default as CardGrid } from './CardGrid';
export { default as CardList } from './CardList';
export { default as PageSection } from './PageSection';
export { default as ResponsiveLayout } from './ResponsiveLayout';

// App framework components
export { default as MainLayout } from './MainLayout';
export { default as Header } from './Header';
export { default as Footer } from './Footer';
export { default as FolderSidebar } from './FolderSidebar';
export { default as Logo } from './Logo';

// Re-export all layout components as a default object for specific imports
const Layout = {
  Container,
  ContentPadding,
  Stack,
  Cluster,
  Grid,
  SplitLayout,
  PageLayout,
  CardGrid,
  CardList,
  PageSection,
  ResponsiveLayout,
  MainLayout,
  Header,
  Footer,
  FolderSidebar,
  Logo,
};

export default Layout;
