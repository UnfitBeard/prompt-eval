import { TestBed } from '@angular/core/testing';

import { PromptEvalStateService } from './prompt-eval-state.service';

describe('PromptEvalStateService', () => {
  let service: PromptEvalStateService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PromptEvalStateService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
