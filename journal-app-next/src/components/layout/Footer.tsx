'use client';

import React from 'react';
import Container from './Container';
import Cluster from './Cluster';
import { cn } from '@/lib/utils';

const Footer: React.FC = () => {
  return (
    <footer
      className="border-t border-border py-6"
      style={{ backgroundColor: 'var(--footer-background, var(--background))' }}
    >
      <Container>
        <Cluster
          justify="between"
          align="center"
          className="flex-col md:flex-row"
        >
          <p className="text-muted-foreground text-sm">
            © {new Date().getFullYear()} Journal App. All rights reserved.
          </p>
          <div className="mt-4 md:mt-0">
            <Cluster gap="md">
              <a
                href="#"
                className="text-muted-foreground hover:text-primary text-sm transition-colors"
              >
                Privacy Policy
              </a>
              <a
                href="#"
                className="text-muted-foreground hover:text-primary text-sm transition-colors"
              >
                Terms of Service
              </a>
            </Cluster>
          </div>
        </Cluster>
      </Container>
    </footer>
  );
};

export default Footer;
