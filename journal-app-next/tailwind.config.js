/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: {
          DEFAULT: 'var(--primary)',
          foreground: 'var(--primary-foreground)',
        },
        secondary: {
          DEFAULT: 'var(--secondary)',
          foreground: 'var(--secondary-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        border: 'var(--border)',
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        ring: 'var(--ring)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '100%',
            ul: {
              listStyleType: 'disc',
              paddingLeft: '1.5rem',
            },
            ol: {
              listStyleType: 'decimal',
              paddingLeft: '1.5rem',
            },
            li: {
              marginTop: '0.25rem',
              marginBottom: '0.25rem',
            },
            'ul > li::marker': {
              color: 'var(--foreground)',
            },
            'ol > li::marker': {
              color: 'var(--foreground)',
            },
            h1: {
              fontSize: '2rem',
              fontWeight: '700',
              marginTop: '1.5rem',
              marginBottom: '1rem',
              paddingBottom: '0.5rem',
              borderBottom: '1px solid var(--border)',
              color: 'var(--foreground)',
              lineHeight: '1.2',
            },
            h2: {
              fontSize: '1.75rem',
              fontWeight: '600',
              marginTop: '1.25rem',
              marginBottom: '0.75rem',
              color: 'var(--foreground)',
              lineHeight: '1.3',
            },
            h3: {
              fontSize: '1.5rem',
              fontWeight: '500',
              marginTop: '1rem',
              marginBottom: '0.5rem',
              color: 'var(--foreground)',
              lineHeight: '1.4',
            },
            h4: {
              fontSize: '1.25rem',
              fontWeight: '500',
              marginTop: '1rem',
              marginBottom: '0.5rem',
              color: 'var(--foreground)',
            },
            h5: {
              fontSize: '1.1rem',
              fontWeight: '500',
              marginTop: '0.75rem',
              marginBottom: '0.5rem',
              color: 'var(--foreground)',
            },
            h6: {
              fontSize: '1rem',
              fontWeight: '500',
              marginTop: '0.75rem',
              marginBottom: '0.5rem',
              color: 'var(--muted-foreground)',
            }
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
    },
  },
  plugins: [
    import('@tailwindcss/typography'),
    import('tailwindcss-animate'),
  ],
}
