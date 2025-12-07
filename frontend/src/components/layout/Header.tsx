'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import styles from './Header.module.css';

interface HeaderProps {
  forumName?: string;
  isLoggedIn?: boolean;
  username?: string;
}

/**
 * Forum Header - phpBB 2.x style
 * Contains logo, welcome message, and main navigation
 */
export default function Header({
  forumName = 'Cursed Board',
  isLoggedIn = false,
  username = 'Guest',
}: HeaderProps) {
  // Use static date to avoid hydration mismatch, update on client
  const [currentDate, setCurrentDate] = useState('Sun Dec 03, 2006');

  useEffect(() => {
    setCurrentDate(new Date().toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }));
  }, []);

  return (
    <header className={styles.header}>
      {/* Top bar with login links */}
      <div className={styles.topBar}>
        <table className={styles.topTable}>
          <tbody>
            <tr>
              <td className={styles.welcomeCell}>
                {isLoggedIn ? (
                  <>
                    Welcome back, <strong>{username}</strong>!
                    {' '}
                    <Link href="/messages">Messages</Link>
                    {' | '}
                    <Link href="/profile">Profile</Link>
                    {' | '}
                    <Link href="/logout">Logout</Link>
                  </>
                ) : (
                  <>
                    Welcome, Guest!
                    {' '}
                    <Link href="/login">Login</Link>
                    {' | '}
                    <Link href="/register">Register</Link>
                  </>
                )}
              </td>
              <td className={styles.dateCell}>
                {currentDate}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Main header with logo */}
      <div className={styles.mainHeader}>
        <table className={styles.logoTable}>
          <tbody>
            <tr>
              <td className={styles.logoCell}>
                <Link href="/" className={styles.logoLink}>
                  <h1 className={styles.forumTitle}>{forumName}</h1>
                  <span className={styles.forumSubtitle}>
                    Community Forum of [REDACTED]
                  </span>
                </Link>
              </td>
              <td className={styles.searchCell}>
                <form className={styles.searchForm} action="/search" method="get">
                  <input
                    type="text"
                    name="q"
                    placeholder="Search..."
                    className={styles.searchInput}
                  />
                  <button type="submit" className={styles.searchButton}>
                    Go
                  </button>
                </form>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Navigation bar */}
      <nav className={styles.navBar}>
        <table className={styles.navTable}>
          <tbody>
            <tr>
              <td>
                <Link href="/" className={styles.navLink}>
                  <span className={styles.navIcon}>🏠</span>
                  Forum Index
                </Link>
              </td>
              <td>
                <Link href="/members" className={styles.navLink}>
                  <span className={styles.navIcon}>👥</span>
                  Members
                </Link>
              </td>
              <td>
                <Link href="/rules" className={styles.navLink}>
                  <span className={styles.navIcon}>📋</span>
                  Rules
                </Link>
              </td>
              <td>
                <Link href="/search" className={styles.navLink}>
                  <span className={styles.navIcon}>🔍</span>
                  Search
                </Link>
              </td>
              {isLoggedIn && (
                <td>
                  <Link href="/messages" className={styles.navLink}>
                    <span className={styles.navIcon}>✉️</span>
                    Private Messages
                  </Link>
                </td>
              )}
            </tr>
          </tbody>
        </table>
      </nav>
    </header>
  );
}
