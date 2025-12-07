'use client';

import Link from 'next/link';
import styles from './Navigation.module.css';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface NavigationProps {
  breadcrumbs?: BreadcrumbItem[];
  showHomeLink?: boolean;
}

/**
 * Breadcrumb Navigation - phpBB style
 * Shows path like: Forum Index » General » Topic Title
 */
export default function Navigation({
  breadcrumbs = [],
  showHomeLink = true,
}: NavigationProps) {
  const allBreadcrumbs: BreadcrumbItem[] = showHomeLink
    ? [{ label: 'Forum Index', href: '/' }, ...breadcrumbs]
    : breadcrumbs;

  if (allBreadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav className={styles.navigation} aria-label="Breadcrumb">
      <div className={styles.breadcrumbs}>
        {allBreadcrumbs.map((item, index) => (
          <span key={index}>
            {index > 0 && (
              <span className={styles.separator}>»</span>
            )}
            {item.href && index < allBreadcrumbs.length - 1 ? (
              <Link href={item.href} className={styles.link}>
                {item.label}
              </Link>
            ) : (
              <span className={styles.current}>{item.label}</span>
            )}
          </span>
        ))}
      </div>
    </nav>
  );
}
