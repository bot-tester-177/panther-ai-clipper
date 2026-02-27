import '../styles/globals.css';
import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function App({ Component, pageProps }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = window.localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, []);

  const logout = () => {
    window.localStorage.removeItem('token');
    setIsLoggedIn(false);
    window.location.href = '/login';
  };

  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <nav className="bg-cyber-bg p-4 text-cyber-green font-mono flex justify-between">
        <div>
          {/* next.js 13 Link no longer accepts an <a> child by default, so
              apply styling directly or use legacyBehavior if you prefer
              to keep the old pattern. */}
          <Link href="/dashboard" className="mr-4">
            Dashboard
          </Link>
          <Link href="/clips">
            Clips
          </Link>
        </div>
        <div>
          {isLoggedIn ? (
            <button onClick={logout} className="underline">
              Logout
            </button>
          ) : (
            <>
              <Link href="/login" className="mr-4 underline">
                Login
              </Link>
              <Link href="/register" className="underline">
                Register
              </Link>
            </>
          )}
        </div>
      </nav>
      <Component {...pageProps} />
    </>
  );
}
