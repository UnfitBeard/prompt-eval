import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

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

@Injectable({
  providedIn: 'root',
})
export class TemplatesService {
  private templatesURL = `http://localhost:10000/api/v1/prompts/get-templates`;
  constructor(private http: HttpClient) {}

  getTemplates(): Observable<PromptsResponse> {
    return this.http.post<PromptsResponse>(
      this.templatesURL,
      {},
      {
        withCredentials: true,
      }
    );
  }
}
