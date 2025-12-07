import Link from 'next/link';
import { Navigation } from '@/components/layout';
import styles from './page.module.css';

// Mock post data
const mockPosts = [
  {
    id: 1,
    postNumber: 1,
    author: {
      username: 'sergey1978',
      avatar: null,
      role: 'Member',
      postCount: 156,
      joinDate: 'Sep 2003',
      location: 'Downtown',
    },
    content: `Has anyone else noticed the strange noises coming from the old factory on the edge of town?

I was walking my dog last night around 11 PM and I heard what sounded like... machinery? But the factory has been closed since 2001.

The dog was really agitated. Wouldn't stop barking at the building.

Just wondering if I'm going crazy or if anyone else has heard this.`,
    createdAt: 'Thu Nov 30, 2006 11:59 pm',
    isEdited: false,
  },
  {
    id: 2,
    postNumber: 2,
    author: {
      username: 'marina_k',
      avatar: null,
      role: 'Senior Member',
      postCount: 289,
      joinDate: 'Mar 2004',
      location: null,
    },
    content: `I haven't heard anything, but my apartment is on the other side of town.

That factory has been abandoned for years though. Maybe it was just the wind? Old buildings make strange sounds.

Or maybe homeless people are using it as shelter?`,
    createdAt: 'Fri Dec 01, 2006 8:15 am',
    isEdited: false,
  },
  {
    id: 3,
    postNumber: 3,
    author: {
      username: 'guest_2005',
      avatar: null,
      role: 'Member',
      postCount: 45,
      joinDate: 'Jan 2005',
      location: 'Near the factory',
    },
    content: `Actually... yes. I live pretty close to that area.

I've been hearing things for about a week now. Always late at night. Around 2-3 AM.

It doesn't sound like wind to me. More like... humming? Low frequency. Sometimes my windows rattle.

I called the police but they said they'd "look into it" and never got back to me.`,
    createdAt: 'Fri Dec 01, 2006 12:30 pm',
    isEdited: false,
  },
  {
    id: 4,
    postNumber: 4,
    author: {
      username: 'admin',
      avatar: null,
      role: 'Administrator',
      postCount: 342,
      joinDate: 'Jan 2003',
      location: null,
    },
    content: `Let's keep this civil and factual. No conspiracy theories please.

If you're concerned about the factory, I'd suggest contacting city hall during business hours. They should have records about the property.

There might be a simple explanation - perhaps they're doing some kind of maintenance or renovation work.`,
    createdAt: 'Fri Dec 01, 2006 2:00 pm',
    isEdited: true,
    editedAt: 'Fri Dec 01, 2006 2:05 pm',
  },
  {
    id: 5,
    postNumber: 5,
    author: {
      username: '█████',
      avatar: null,
      role: 'Member',
      postCount: 3,
      joinDate: 'Nov 2006',
      location: '̷̧̛̺͎̮̪̮̪̫̦̼̗̟̱̟̫̠͎̞̗̜̮̯̪̦̫̦͓̲̫̹̤̰̼͙̟̱̟̫̠̪̮̪̫̦̼̗͎̮̪̮̯̪̦',
    },
    content: `do not go there at night

do not go there at night

do not go there at night

they are listening`,
    createdAt: 'Fri Dec 01, 2006 3:33 am',
    isEdited: false,
  },
  {
    id: 6,
    postNumber: 6,
    author: {
      username: 'sergey1978',
      avatar: null,
      role: 'Member',
      postCount: 156,
      joinDate: 'Sep 2003',
      location: 'Downtown',
    },
    content: `@admin - I tried calling city hall. They said there's no scheduled work at that location. The property is still listed as abandoned.

@guest_2005 - The window rattling thing is creepy. Now I'm a bit worried.

@█████ - ...what? Who are you? Your account was created last week.`,
    createdAt: 'Fri Dec 01, 2006 5:45 pm',
    isEdited: false,
  },
  {
    id: 7,
    postNumber: 7,
    author: {
      username: '[deleted]',
      avatar: null,
      role: 'Member',
      postCount: 0,
      joinDate: 'ERROR',
      location: null,
    },
    content: `[This post has been removed by a moderator]`,
    createdAt: 'Sat Dec 01, 2006 3:33 am',
    isEdited: false,
    isDeleted: true,
  },
];

const mockThread = {
  id: 5,
  title: 'Strange noises from the old factory',
  board: { slug: 'general', name: 'General Discussion' },
  isLocked: false,
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ThreadPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <div className={styles.container}>
      <Navigation
        breadcrumbs={[
          { label: mockThread.board.name, href: `/board/${mockThread.board.slug}` },
          { label: mockThread.title },
        ]}
      />

      {/* Thread title */}
      <div className={styles.threadHeader}>
        <h2 className={styles.threadTitle}>{mockThread.title}</h2>
      </div>

      {/* Post actions */}
      <div className={styles.actions}>
        {!mockThread.isLocked && (
          <Link href={`/thread/${id}/reply`} className={styles.replyBtn}>
            ✏️ Post Reply
          </Link>
        )}
        {mockThread.isLocked && (
          <span className={styles.lockedNotice}>🔒 This topic is locked</span>
        )}
      </div>

      {/* Posts */}
      <div className={styles.posts}>
        {mockPosts.map((post) => (
          <div key={post.id} className={`${styles.post} ${post.isDeleted ? styles.deleted : ''}`}>
            <table className={styles.postTable}>
              <tbody>
                <tr>
                  {/* Author info */}
                  <td className={styles.authorColumn}>
                    <div className={styles.authorInfo}>
                      <Link href={`/user/${post.author.username}`} className={styles.authorName}>
                        {post.author.username}
                      </Link>
                      <div className={styles.authorRole}>{post.author.role}</div>
                      <div className={styles.authorAvatar}>
                        {post.author.avatar ? (
                          <img src={post.author.avatar} alt="" />
                        ) : (
                          <div className={styles.defaultAvatar}>👤</div>
                        )}
                      </div>
                      <div className={styles.authorStats}>
                        <div>Posts: {post.author.postCount}</div>
                        <div>Joined: {post.author.joinDate}</div>
                        {post.author.location && (
                          <div>Location: {post.author.location}</div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Post content */}
                  <td className={styles.contentColumn}>
                    <div className={styles.postHeader}>
                      <span className={styles.postNumber}>#{post.postNumber}</span>
                      <span className={styles.postDate}>
                        Posted: {post.createdAt}
                      </span>
                    </div>
                    <div className={styles.postContent}>
                      {post.content.split('\n').map((line, i) => (
                        <p key={i}>{line || <br />}</p>
                      ))}
                    </div>
                    {post.isEdited && (
                      <div className={styles.editNotice}>
                        Last edited by {post.author.username} on {post.editedAt}
                      </div>
                    )}
                    <div className={styles.postActions}>
                      <Link href={`/thread/${id}/quote/${post.id}`}>Quote</Link>
                      {' | '}
                      <Link href={`/report/${post.id}`}>Report</Link>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className={styles.pagination}>
        <span className={styles.pageInfo}>Page 1 of 1</span>
      </div>

      {/* Reply form */}
      {!mockThread.isLocked && (
        <div className={styles.replyForm}>
          <table className={styles.replyTable}>
            <tbody>
              <tr>
                <td className={styles.replyHeader} colSpan={2}>
                  Quick Reply
                </td>
              </tr>
              <tr>
                <td className={styles.replyLabel}>Message:</td>
                <td className={styles.replyInput}>
                  <textarea
                    className={styles.replyTextarea}
                    rows={6}
                    placeholder="Type your reply here..."
                  />
                </td>
              </tr>
              <tr>
                <td></td>
                <td className={styles.replySubmit}>
                  <button type="submit" className={styles.submitBtn}>
                    Submit
                  </button>
                  <button type="button" className={styles.previewBtn}>
                    Preview
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Bottom actions */}
      <div className={styles.actions}>
        {!mockThread.isLocked && (
          <Link href={`/thread/${id}/reply`} className={styles.replyBtn}>
            ✏️ Post Reply
          </Link>
        )}
      </div>
    </div>
  );
}
