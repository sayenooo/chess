import { Component, inject, OnInit, afterNextRender, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService, UserProfile } from '../../services/api.service';
import { HomeComponent } from './sections/home/home.component';
import { PlayComponent } from './sections/play/play.component';
import { LearnComponent } from './sections/learn/learn.component';
import { NewsComponent } from './sections/news/news.component';

import { FormsModule } from '@angular/forms';

type Section = 'main' | 'play' | 'learn' | 'news';

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, FormsModule, HomeComponent, PlayComponent, LearnComponent, NewsComponent],
  templateUrl: './main-layout.component.html',
  styleUrl: './main-layout.component.css'
})
export class MainLayoutComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  activeSection: Section = 'main';
  profileOpen = false;
  user: UserProfile | null = null;
  isGameLocked = false;
  lockNotification = '';

  readonly navItems: { key: Section; label: string; icon: string }[] = [
    { key: 'main', label: 'Main', icon: '♟' },
    { key: 'play', label: 'Play', icon: '♞' },
    { key: 'learn', label: 'Learn', icon: '♝' },
    { key: 'news', label: 'News', icon: '♜' },
  ];

  constructor() {
    afterNextRender(() => {
      this.loadProfile();
    });
  }

  ngOnInit() {}

  loadProfile() {
    this.api.getProfile().subscribe({
      next: (user) => {
        this.user = user;
        this.cdr.markForCheck();
      },
      error: () => {
        this.api.logout();
        this.router.navigate(['/auth']);
      }
    });
  }

  setSection(section: Section) {
    if (this.isGameLocked && section !== 'play') {
      this.lockNotification = 'You cannot leave while a game is in progress!';
      setTimeout(() => this.lockNotification = '', 3000);
      return;
    }
    this.activeSection = section;
  }

  toggleProfile() {
    this.profileOpen = !this.profileOpen;
  }

  closeProfile() {
    this.profileOpen = false;
  }

  logout() {
    this.api.logout();
    this.router.navigate(['/auth']);
  }

  get displayName(): string {
    return this.user?.username ?? 'Player';
  }

  get displayRating(): number {
    return this.user?.player_profile?.rating ?? 500;
  }

  get avatarUrl(): string | null {
    const avatar = this.user?.player_profile?.avatar;
    if (!avatar) return null;
    // If it starts with http, it's a full URL; otherwise prepend backend
    return avatar.startsWith('http') ? avatar : `http://127.0.0.1:8000${avatar}`;
  }

  uploadingAvatar = false;

  onAvatarChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;
    const file = input.files[0];
    this.uploadingAvatar = true;
    this.api.uploadAvatar(file).subscribe({
      next: (res) => {
        if (this.user) {
          this.user.player_profile.avatar = res.avatar;
        }
        this.uploadingAvatar = false;
      },
      error: () => (this.uploadingAvatar = false)
    });
  }

  deleteAvatar() {
    this.api.deleteAvatar().subscribe(() => {
      if (this.user) {
        this.user.player_profile.avatar = null;
      }
    });
  }

  editingUsername = false;
  newUsername = '';

  startEditUsername() {
    this.editingUsername = true;
    this.newUsername = this.user?.username ?? '';
  }

  saveUsername() {
    if (!this.newUsername.trim() || this.newUsername === this.user?.username) {
      this.editingUsername = false;
      return;
    }
    this.api.updateUsername(this.newUsername).subscribe({
      next: (res) => {
        if (this.user) this.user.username = res.username;
        this.editingUsername = false;
      },
      error: (err) => {
        alert(err.error?.error || 'Failed to update username');
      }
    });
  }

  cancelEditUsername() {
    this.editingUsername = false;
  }
}
