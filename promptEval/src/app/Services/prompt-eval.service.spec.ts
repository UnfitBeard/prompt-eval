import { TestBed } from '@angular/core/testing';

import { PromptEvalService } from './prompt-eval.service';

describe('PromptEvalService', () => {
  let service: PromptEvalService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PromptEvalService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
