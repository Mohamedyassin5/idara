import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { firstValueFrom } from 'rxjs';

export interface User {
  id: number;
  name: string;
  email: string;
}

interface AuthResponse {
  access_token: string;
  user: User;
}

const TOKEN_KEY = 'idara.token';
const USER_KEY = 'idara.user';

@Injectable({ providedIn: 'root' })
export class Auth {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  readonly token = signal<string | null>(this.read(TOKEN_KEY));
  readonly user = signal<User | null>(this.readUser());
  readonly loggedIn = computed(() => !!this.token());

  async login(email: string, password: string): Promise<void> {
    this.store(await firstValueFrom(this.http.post<AuthResponse>('/api/auth/login', { email, password })));
  }

  async register(name: string, email: string, password: string): Promise<void> {
    this.store(await firstValueFrom(this.http.post<AuthResponse>('/api/auth/register', { name, email, password })));
  }

  logout(redirect = true): void {
    this.token.set(null);
    this.user.set(null);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      /* storage unavailable */
    }
    if (redirect) this.router.navigate(['/login']);
  }

  private store(res: AuthResponse): void {
    this.token.set(res.access_token);
    this.user.set(res.user);
    try {
      localStorage.setItem(TOKEN_KEY, res.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    } catch {
      /* the session just won't survive a reload */
    }
  }

  private read(key: string): string | null {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  private readUser(): User | null {
    try {
      const raw = this.read(USER_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  }
}
