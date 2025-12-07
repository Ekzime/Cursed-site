/**
 * TypeScript types for Cursed Board
 * Matching backend schemas
 */

// =============================================================================
// User Types
// =============================================================================

export interface User {
  id: number;
  username: string;
  email?: string;
  avatar_url?: string;
  signature?: string;
  post_count: number;
  created_at: string; // ISO date
  last_seen?: string;
  role: 'member' | 'moderator' | 'admin';
  is_online?: boolean;
}

export interface UserProfile extends User {
  bio?: string;
  location?: string;
  website?: string;
  joined_date_display: string; // "Mar 2004"
}

// =============================================================================
// Board Types
// =============================================================================

export interface Board {
  id: number;
  slug: string;
  name: string;
  description?: string;
  icon?: string;
  thread_count: number;
  post_count: number;
  last_post?: LastPost;
  is_locked?: boolean;
  sort_order: number;
  parent_id?: number; // for sub-boards
}

export interface BoardCategory {
  id: number;
  name: string;
  boards: Board[];
}

export interface LastPost {
  id: number;
  thread_id: number;
  thread_title: string;
  author: string;
  created_at: string;
}

// =============================================================================
// Thread Types
// =============================================================================

export interface Thread {
  id: number;
  board_id: number;
  title: string;
  author: User;
  created_at: string;
  reply_count: number;
  view_count: number;
  last_post?: LastPost;
  is_pinned: boolean;
  is_locked: boolean;
  is_hot: boolean; // many replies
}

export interface ThreadDetail extends Thread {
  posts: Post[];
  board: Board;
}

// =============================================================================
// Post Types
// =============================================================================

export interface Post {
  id: number;
  thread_id: number;
  author: User;
  content: string;
  created_at: string;
  updated_at?: string;
  is_edited: boolean;
  edit_count?: number;
  // For display
  post_number: number; // #1, #2, etc.
}

// =============================================================================
// Message Types (Private Messages)
// =============================================================================

export interface Message {
  id: number;
  from_user: User;
  to_user: User;
  subject: string;
  content: string;
  created_at: string;
  is_read: boolean;
}

// =============================================================================
// Ritual Engine Types (matching backend)
// =============================================================================

export type ProgressLevel = 'low' | 'medium' | 'high' | 'critical';

export interface RitualState {
  user_id: string;
  progress: number; // 0-100
  level: ProgressLevel;
  viewed_threads: number[];
  viewed_posts: number[];
  time_on_site: number; // seconds
  first_visit: string;
  last_activity: string;
  triggers_hit: string[];
}

// =============================================================================
// Anomaly Types
// =============================================================================

export type AnomalyType =
  | 'glitch'
  | 'whisper'
  | 'presence'
  | 'deja_vu'
  | 'corruption'
  | 'temporal'
  | 'eyes'
  | 'static'
  | 'new_post'
  | 'notification';

export type AnomalySeverity = 'subtle' | 'noticeable' | 'obvious' | 'extreme';

export interface AnomalyEvent {
  id: string;
  type: AnomalyType;
  severity: AnomalySeverity;
  target_id?: number; // post/thread to affect
  data: Record<string, unknown>;
  duration_ms: number;
  timestamp: string;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}

// =============================================================================
// Auth Types
// =============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// =============================================================================
// Forum Stats
// =============================================================================

export interface ForumStats {
  total_users: number;
  total_threads: number;
  total_posts: number;
  newest_member: string;
  online_users: number;
  online_guests: number;
  record_online: number;
  record_date: string;
}
