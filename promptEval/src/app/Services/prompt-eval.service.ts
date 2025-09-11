import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class PromptEvalService {
  backendUrl = 'http://localhost:3000';
  modelUrl = 'http://localhost:5000';

  constructor() {}
}
