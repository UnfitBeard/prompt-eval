import { TestBed } from '@angular/core/testing';

import { PromptEvaluatorV2Service } from './prompt-evaluator-v2.service';

describe('PromptEvaluatorV2Service', () => {
  let service: PromptEvaluatorV2Service;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PromptEvaluatorV2Service);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
