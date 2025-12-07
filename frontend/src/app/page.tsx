import Link from 'next/link';
import styles from './page.module.css';

// Mock data - will be replaced with API calls
const mockBoards = [
  {
    category: 'Community',
    boards: [
      {
        id: 1,
        slug: 'general',
        name: 'General Discussion',
        description: 'Talk about anything and everything',
        threadCount: 234,
        postCount: 1892,
        lastPost: {
          title: 'What do you think about...',
          author: 'marina_k',
          date: 'Sun Dec 03, 2006 4:23 pm',
        },
      },
      {
        id: 2,
        slug: 'introductions',
        name: 'Introductions',
        description: 'New here? Say hello!',
        threadCount: 89,
        postCount: 456,
        lastPost: {
          title: 'Hi everyone',
          author: 'guest_2008',
          date: 'Fri Nov 24, 2006 11:15 am',
        },
      },
    ],
  },
  {
    category: 'Local News',
    boards: [
      {
        id: 3,
        slug: 'news',
        name: 'City News',
        description: 'News and events from our community',
        threadCount: 156,
        postCount: 892,
        lastPost: {
          title: 'Strange lights near the...',
          author: 'sergey1978',
          date: 'Wed Dec 06, 2006 9:47 pm',
        },
      },
      {
        id: 4,
        slug: 'incidents',
        name: 'Incidents',
        description: 'Report and discuss local incidents',
        threadCount: 43,
        postCount: 287,
        lastPost: {
          title: 'Did anyone else hear...',
          author: 'admin',
          date: 'Tue Dec 05, 2006 3:12 am',
        },
        isLocked: false,
      },
    ],
  },
  {
    category: 'Marketplace',
    boards: [
      {
        id: 5,
        slug: 'buy-sell',
        name: 'Buy / Sell',
        description: 'Trade with your neighbors',
        threadCount: 312,
        postCount: 1245,
        lastPost: {
          title: 'Selling old radio...',
          author: 'marina_k',
          date: 'Mon Dec 04, 2006 2:30 pm',
        },
      },
    ],
  },
  {
    category: 'Other',
    boards: [
      {
        id: 6,
        slug: 'off-topic',
        name: 'Off Topic',
        description: 'Random discussions',
        threadCount: 178,
        postCount: 923,
        lastPost: {
          title: 'Weird dream last night',
          author: '█████',
          date: 'Sat Dec 02, 2006 11:59 pm',
        },
      },
      {
        id: 7,
        slug: 'strange',
        name: 'Strange Occurrences',
        description: 'Things that cannot be explained',
        threadCount: 12,
        postCount: 47,
        lastPost: {
          title: '[DELETED]',
          author: '[unknown]',
          date: 'ERROR',
        },
        isLocked: true,
      },
    ],
  },
];

export default function HomePage() {
  return (
    <div className={styles.container}>
      {/* Announcement */}
      <div className={styles.announcement}>
        <table className={styles.announcementTable}>
          <tbody>
            <tr>
              <td className={styles.announcementHeader}>
                📢 Announcement
              </td>
            </tr>
            <tr>
              <td className={styles.announcementContent}>
                Welcome to our community forum! Please read the{' '}
                <Link href="/rules">rules</Link> before posting.
                <br />
                <span className={styles.announcementMeta}>
                  Posted by admin on Mon Jan 05, 2004 10:00 am
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Board Categories */}
      {mockBoards.map((category) => (
        <div key={category.category} className={styles.category}>
          <table className={styles.boardTable}>
            <thead>
              <tr>
                <th className={styles.categoryHeader} colSpan={4}>
                  {category.category}
                </th>
              </tr>
              <tr className={styles.columnHeaders}>
                <th className={styles.colForum}>Forum</th>
                <th className={styles.colTopics}>Topics</th>
                <th className={styles.colPosts}>Posts</th>
                <th className={styles.colLastPost}>Last Post</th>
              </tr>
            </thead>
            <tbody>
              {category.boards.map((board, index) => (
                <tr key={board.id} className={index % 2 === 0 ? styles.row1 : styles.row2}>
                  <td className={styles.forumCell}>
                    <div className={styles.forumIcon}>
                      {board.isLocked ? '🔒' : '📁'}
                    </div>
                    <div className={styles.forumInfo}>
                      <Link href={`/board/${board.slug}`} className={styles.forumName}>
                        {board.name}
                      </Link>
                      <span className={styles.forumDesc}>{board.description}</span>
                    </div>
                  </td>
                  <td className={styles.countCell}>{board.threadCount}</td>
                  <td className={styles.countCell}>{board.postCount}</td>
                  <td className={styles.lastPostCell}>
                    {board.lastPost && (
                      <>
                        <Link href="#" className={styles.lastPostTitle}>
                          {board.lastPost.title.length > 20
                            ? board.lastPost.title.substring(0, 20) + '...'
                            : board.lastPost.title}
                        </Link>
                        <br />
                        <span className={styles.lastPostMeta}>
                          by{' '}
                          <Link href={`/user/${encodeURIComponent(board.lastPost.author)}`}>
                            {board.lastPost.author}
                          </Link>
                          <br />
                          {board.lastPost.date}
                        </span>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      {/* Mark forums read */}
      <div className={styles.actions}>
        <Link href="#" className={styles.actionLink}>
          Mark all forums read
        </Link>
      </div>
    </div>
  );
}
