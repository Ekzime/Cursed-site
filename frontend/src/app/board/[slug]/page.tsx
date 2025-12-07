import Link from 'next/link';
import { Navigation } from '@/components/layout';
import styles from './page.module.css';

// Mock thread data
const mockThreads = [
  {
    id: 1,
    title: 'Welcome to our community!',
    author: { username: 'admin', postCount: 342 },
    createdAt: 'Mon Jan 05, 2004 10:15 am',
    replyCount: 45,
    viewCount: 1234,
    lastPost: {
      author: 'marina_k',
      date: 'Sun Dec 03, 2006 4:23 pm',
    },
    isPinned: true,
    isLocked: false,
    isHot: true,
  },
  {
    id: 2,
    title: 'Rules and Guidelines - READ FIRST',
    author: { username: 'admin', postCount: 342 },
    createdAt: 'Mon Jan 05, 2004 10:30 am',
    replyCount: 0,
    viewCount: 892,
    lastPost: {
      author: 'admin',
      date: 'Mon Jan 05, 2004 10:30 am',
    },
    isPinned: true,
    isLocked: true,
    isHot: false,
  },
  {
    id: 3,
    title: 'What do you think about the new mall?',
    author: { username: 'sergey1978', postCount: 156 },
    createdAt: 'Sat Dec 02, 2006 3:45 pm',
    replyCount: 23,
    viewCount: 445,
    lastPost: {
      author: 'marina_k',
      date: 'Sun Dec 03, 2006 4:23 pm',
    },
    isPinned: false,
    isLocked: false,
    isHot: false,
  },
  {
    id: 4,
    title: 'Has anyone seen the stray cats lately?',
    author: { username: 'marina_k', postCount: 289 },
    createdAt: 'Fri Dec 01, 2006 11:20 am',
    replyCount: 12,
    viewCount: 234,
    lastPost: {
      author: 'guest_2005',
      date: 'Sat Dec 02, 2006 9:15 pm',
    },
    isPinned: false,
    isLocked: false,
    isHot: false,
  },
  {
    id: 5,
    title: 'Strange noises from the old factory',
    author: { username: '█████', postCount: 3 },
    createdAt: 'Thu Nov 30, 2006 11:59 pm',
    replyCount: 7,
    viewCount: 156,
    lastPost: {
      author: '[deleted]',
      date: 'Fri Dec 01, 2006 3:33 am',
    },
    isPinned: false,
    isLocked: false,
    isHot: false,
  },
  {
    id: 6,
    title: 'Best bakery in town?',
    author: { username: 'guest_2005', postCount: 45 },
    createdAt: 'Wed Nov 29, 2006 2:30 pm',
    replyCount: 34,
    viewCount: 567,
    lastPost: {
      author: 'sergey1978',
      date: 'Thu Nov 30, 2006 6:45 pm',
    },
    isPinned: false,
    isLocked: false,
    isHot: true,
  },
  {
    id: 7,
    title: 'Does anyone remember the incident in 2003?',
    author: { username: 'sergey1978', postCount: 156 },
    createdAt: 'Tue Nov 28, 2006 8:00 pm',
    replyCount: 2,
    viewCount: 89,
    lastPost: {
      author: 'admin',
      date: 'Wed Nov 29, 2006 9:00 am',
    },
    isPinned: false,
    isLocked: true,
    isHot: false,
  },
];

// Mock board data
const mockBoards: Record<string, { name: string; description: string }> = {
  general: { name: 'General Discussion', description: 'Talk about anything and everything' },
  introductions: { name: 'Introductions', description: 'New here? Say hello!' },
  news: { name: 'City News', description: 'News and events from our community' },
  incidents: { name: 'Incidents', description: 'Report and discuss local incidents' },
  'buy-sell': { name: 'Buy / Sell', description: 'Trade with your neighbors' },
  'off-topic': { name: 'Off Topic', description: 'Random discussions' },
  strange: { name: 'Strange Occurrences', description: 'Things that cannot be explained' },
};

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function BoardPage({ params }: PageProps) {
  const { slug } = await params;
  const board = mockBoards[slug] || { name: 'Unknown Board', description: '' };

  const getThreadIcon = (thread: typeof mockThreads[0]) => {
    if (thread.isLocked) return '🔒';
    if (thread.isPinned) return '📌';
    if (thread.isHot) return '🔥';
    return '📄';
  };

  return (
    <div className={styles.container}>
      <Navigation
        breadcrumbs={[
          { label: board.name },
        ]}
      />

      {/* Board header */}
      <div className={styles.boardHeader}>
        <h2 className={styles.boardTitle}>{board.name}</h2>
        <p className={styles.boardDesc}>{board.description}</p>
      </div>

      {/* New topic button */}
      <div className={styles.actions}>
        <Link href={`/board/${slug}/new`} className={styles.newTopicBtn}>
          📝 New Topic
        </Link>
      </div>

      {/* Thread list */}
      <table className={styles.threadTable}>
        <thead>
          <tr className={styles.columnHeaders}>
            <th className={styles.colIcon}></th>
            <th className={styles.colTopic}>Topics</th>
            <th className={styles.colAuthor}>Author</th>
            <th className={styles.colReplies}>Replies</th>
            <th className={styles.colViews}>Views</th>
            <th className={styles.colLastPost}>Last Post</th>
          </tr>
        </thead>
        <tbody>
          {mockThreads.map((thread, index) => (
            <tr
              key={thread.id}
              className={`${index % 2 === 0 ? styles.row1 : styles.row2} ${thread.isPinned ? styles.pinned : ''}`}
            >
              <td className={styles.iconCell}>
                <span className={styles.threadIcon}>{getThreadIcon(thread)}</span>
              </td>
              <td className={styles.topicCell}>
                <Link href={`/thread/${thread.id}`} className={styles.topicLink}>
                  {thread.isPinned && <span className={styles.badge}>Sticky:</span>}
                  {thread.isLocked && <span className={styles.badgeLocked}>[Locked]</span>}
                  {thread.title}
                </Link>
                {thread.replyCount > 20 && (
                  <span className={styles.pageLinks}>
                    [ <Link href={`/thread/${thread.id}?page=1`}>1</Link>
                    {' '}<Link href={`/thread/${thread.id}?page=2`}>2</Link>
                    {thread.replyCount > 40 && <> ... <Link href={`/thread/${thread.id}?page=last`}>Last</Link></>}
                    {' '}]
                  </span>
                )}
              </td>
              <td className={styles.authorCell}>
                <Link href={`/user/${thread.author.username}`}>
                  {thread.author.username}
                </Link>
              </td>
              <td className={styles.countCell}>{thread.replyCount}</td>
              <td className={styles.countCell}>{thread.viewCount}</td>
              <td className={styles.lastPostCell}>
                <Link href={`/user/${thread.lastPost.author}`}>
                  {thread.lastPost.author}
                </Link>
                <br />
                <span className={styles.lastPostDate}>{thread.lastPost.date}</span>
                {' '}
                <Link href={`/thread/${thread.id}#last`} className={styles.gotoLink}>
                  ↗
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      <div className={styles.pagination}>
        <span className={styles.pageInfo}>Page 1 of 1</span>
      </div>

      {/* Bottom actions */}
      <div className={styles.actions}>
        <Link href={`/board/${slug}/new`} className={styles.newTopicBtn}>
          📝 New Topic
        </Link>
      </div>
    </div>
  );
}
