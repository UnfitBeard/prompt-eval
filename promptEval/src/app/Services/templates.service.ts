import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

export interface PromptsResponse {
  message: string;
  templates: Template[];
}

export interface Template {
  stats: Stats;
  _id: string;
  title?: string; // optional since not all templates had it
  description?: string; // optional since not all templates had it
  domain: string;
  category: string;
  difficulty: string;
  content: string;
  tags: string[];
  status: string;
  createdBy: string;
  createdAt: string; // ISO string → can be cast to Date later
  updatedAt: string;
  __v: number;
}

export interface Stats {
  uses: number;
  avgScore: number;
}

export interface TemplateCreate {
  title: string;
  description?: string;
  domain: string;
  category: string;
  difficulty: string;
  prompt: string;
  tags?: string[];
  include_eval?: boolean;
}

export interface TemplateCreateResponse {
  success: boolean;
  data: {
    template_id: string;
    message: string;
  };
}

@Injectable({
  providedIn: 'root',
})
export class TemplatesService {
  private apiUrl = environment.apiUrl;
  private apiPrefix = '/api/v1';

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  // getTemplates(): Observable<PromptsResponse> {
  //   // Keep backward compatibility with old endpoint
  //   return this.http.post<PromptsResponse>(
  //     `http://localhost:10000/api/v1/prompts/get-templates`,
  //     {},
  //     {
  //       withCredentials: true,
  //     },
  //   );
  // }

  createTemplate(template: TemplateCreate): Observable<TemplateCreateResponse> {
    return this.http.post<TemplateCreateResponse>(
      `${this.apiUrl}${this.apiPrefix}/templates/create`,
      template,
      {
        headers: this.getHeaders(),
      },
    );
  }

  getTemplatesList(
    domain?: string,
    category?: string,
    difficulty?: string,
  ): Observable<any> {
    const params: any = {};
    if (domain) params.domain = domain;
    if (category) params.category = category;
    if (difficulty) params.difficulty = difficulty;

    return this.http.get<{ success: boolean; data: Template[] }>(
      `${this.apiUrl}${this.apiPrefix}/templates/list`,
      {
        headers: this.getHeaders(),
        params,
      },
    );
  }
}
