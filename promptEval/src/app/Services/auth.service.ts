import { HttpClient, HttpResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of, shareReplay, tap } from 'rxjs';

interface LoginResponse {
  message: string;
  user: {
    id: string;
    email: string;
    fullName: string;
  };
  token: {
    accessToken: string;
    refreshToken: string;
  };
}

interface LoginDto {
  email: string;
  password: string;
}

interface RegisterData {
  fullName: string;
  email: string;
  password: string;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private isAuthenticated = false;
  private authUrl = `http://localhost:10000/api/v1/auth`;

  constructor(private http: HttpClient) {}

  register(registerData: RegisterData): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.authUrl}/register`, registerData, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          localStorage.setItem('access_token', response.token.accessToken);
        }),
        shareReplay(1) //caching last emission far late subscribers
      );
  }

  login(loginData: LoginDto): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.authUrl}/login`, loginData, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          localStorage.setItem('access_token', response.token.accessToken);
        }),
        shareReplay(1) //caching last emission far late subscribers
      );
  }

  logout() {
    this.clearToken;
  }

  get token(): String | null {
    return localStorage.getItem('access_token');
  }

  clearToken() {
    localStorage.removeItem('access_token');
  }
}
