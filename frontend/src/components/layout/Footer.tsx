'use client';

import Link from 'next/link';
import styles from './Footer.module.css';

interface FooterProps {
  showStats?: boolean;
  totalUsers?: number;
  totalPosts?: number;
  newestMember?: string;
}

/**
 * Forum Footer - phpBB 2.x style
 * Statistics, timezone, copyright
 */
export default function Footer({
  showStats = true,
  totalUsers = 127,
  totalPosts = 3842,
  newestMember = 'guest_2008',
}: FooterProps) {
  // Generate a "last active" time that's always in the past
  const getLastActiveTime = () => {
    const options: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
    };
    return new Date().toLocaleTimeString('en-US', options);
  };

  return (
    <footer className={styles.footer}>
      {/* Statistics box */}
      {showStats && (
        <div className={styles.statsBox}>
          <table className={styles.statsTable}>
            <tbody>
              <tr>
                <td className={styles.statsHeader} colSpan={2}>
                  Forum Statistics
                </td>
              </tr>
              <tr className={styles.statsRow}>
                <td>
                  Our members have made a total of{' '}
                  <strong>{totalPosts.toLocaleString()}</strong> posts
                </td>
                <td>
                  We have <strong>{totalUsers.toLocaleString()}</strong>{' '}
                  registered members
                </td>
              </tr>
              <tr className={styles.statsRow}>
                <td colSpan={2}>
                  The newest member is{' '}
                  <Link href={`/user/${newestMember}`} className={styles.memberLink}>
                    {newestMember}
                  </Link>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Who's online - classic phpBB feature */}
      <div className={styles.onlineBox}>
        <table className={styles.onlineTable}>
          <tbody>
            <tr>
              <td className={styles.onlineHeader}>
                Who Is Online
              </td>
            </tr>
            <tr>
              <td className={styles.onlineContent}>
                <span className={styles.onlineIcon}>👤</span>
                In total there are <strong>3</strong> users online ::
                1 Registered, 0 Hidden and 2 Guests
                <br />
                <span className={styles.onlineSmall}>
                  Most users ever online was <strong>47</strong> on Sun Mar 14, 2004 2:34 am
                </span>
                <br />
                <span className={styles.onlineSmall}>
                  Registered Users: None
                </span>
              </td>
            </tr>
            <tr>
              <td className={styles.onlineLegend}>
                <span className={styles.legendItem}>
                  <span className={styles.legendIcon}>📂</span> New posts
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendIcon}>📁</span> No new posts
                </span>
                <span className={styles.legendItem}>
                  <span className={styles.legendIcon}>🔒</span> Locked
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Timezone / Jump to */}
      <div className={styles.bottomBar}>
        <table className={styles.bottomTable}>
          <tbody>
            <tr>
              <td className={styles.timezoneCell}>
                All times are GMT - 5 Hours
              </td>
              <td className={styles.jumpCell}>
                <select className={styles.jumpSelect} defaultValue="">
                  <option value="">Jump to:</option>
                  <option value="general">General Discussion</option>
                  <option value="news">City News</option>
                  <option value="market">Marketplace</option>
                </select>
                <button className={styles.jumpButton}>Go</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Copyright / Powered by */}
      <div className={styles.copyright}>
        <p>
          Powered by{' '}
          <Link href="#" className={styles.poweredLink}>
            phpBB
          </Link>{' '}
          © 2001, 2002 phpBB Group
        </p>
        <p className={styles.disclaimer}>
          This forum and its content are provided as-is.
          <br />
          <span className={styles.lastUpdate}>
            Last database update: {getLastActiveTime()}
          </span>
        </p>
      </div>
    </footer>
  );
}
