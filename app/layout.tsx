import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Growth OS',
  description: 'Evidence-first partner discovery for Growth and GTM teams.',
  openGraph: {
    title: 'Growth OS',
    description: 'From ICP hypothesis to evidence-backed partner discovery.',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'Growth OS',
    description: 'From ICP hypothesis to evidence-backed partner discovery.',
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
