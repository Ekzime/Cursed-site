import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Header, Footer } from '@/components/layout';
import { AnomalyProvider, AnomalyTestPanel } from '@/components/anomaly';

export const metadata: Metadata = {
  title: 'Cursed Board - Community Forum',
  description: 'Community Forum of [REDACTED]. Est. 2003.',
  // Fake old meta tags for authenticity
  other: {
    'generator': 'phpBB 2.0.22',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        {/* Fake old-school meta tags */}
        <meta name="robots" content="index, follow" />
        <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
      </head>
      <body>
        <AnomalyProvider>
          <div className="page-wrapper">
            <Header forumName="Cursed Board" />
            <main>
              {children}
            </main>
            <Footer />
          </div>
          <AnomalyTestPanel />
        </AnomalyProvider>
      </body>
    </html>
  );
}
