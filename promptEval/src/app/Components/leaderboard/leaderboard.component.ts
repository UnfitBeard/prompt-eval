// Components/leaderboard/leaderboard.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ApiService } from '../../Service/api.service';

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  xp: number;
  level: string;
  streak_days: number;
  avatar_url?: string;
  is_current_user?: boolean;
}

@Component({
  selector: 'app-leaderboard',
  imports: [CommonModule],
  templateUrl: './leaderboard.component.html',
  styleUrl: './leaderboard.component.css',
})
export class LeaderboardComponent implements OnInit {
  private api = inject(ApiService);
  
  loading = true;
  error: string | null = null;
  leaderboard: LeaderboardEntry[] = [];
  currentUserRank: number | null = null;

  ngOnInit() {
    this.loadLeaderboard();
  }

  loadLeaderboard() {
    this.loading = true;
    this.error = null;

    this.api.get<LeaderboardEntry[]>('/progress/leaderboard', { limit: 50 }).subscribe({
      next: (entries) => {
        this.leaderboard = entries;
        const currentUser = entries.find(e => e.is_current_user);
        if (currentUser) {
          this.currentUserRank = currentUser.rank;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading leaderboard:', err);
        this.error = 'Failed to load leaderboard';
        this.loading = false;
      },
    });
  }

  getRankBadge(rank: number): string {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  }

  getLevelColor(level: string): string {
    switch (level.toLowerCase()) {
      case 'expert':
        return 'text-purple-600';
      case 'advanced':
        return 'text-blue-600';
      case 'intermediate':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  }

  getInitials(username: string): string {
    return username
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  }
}

