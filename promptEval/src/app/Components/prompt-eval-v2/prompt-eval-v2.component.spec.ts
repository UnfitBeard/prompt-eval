import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptEvalV2Component } from './prompt-eval-v2.component';

describe('PromptEvalV2Component', () => {
  let component: PromptEvalV2Component;
  let fixture: ComponentFixture<PromptEvalV2Component>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PromptEvalV2Component]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PromptEvalV2Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
