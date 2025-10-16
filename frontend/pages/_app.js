import '../styles/globals.css';
import dynamic from 'next/dynamic';

const GlobalErrorBoundary = dynamic(() => import('../components/GlobalErrorBoundary'), { ssr: false });

export default function App({ Component, pageProps }) {
  return (
    <GlobalErrorBoundary>
      <Component {...pageProps} />
    </GlobalErrorBoundary>
  );
}
