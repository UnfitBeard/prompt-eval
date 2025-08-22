import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class PromptEvalService {
  url = 'http://localhost:3000';

  constructor() {}
}
