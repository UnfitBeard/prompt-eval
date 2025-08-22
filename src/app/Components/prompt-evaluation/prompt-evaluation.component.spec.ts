import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptEvaluationComponent } from './prompt-evaluation.component';

describe('PromptEvaluationComponent', () => {
  let component: PromptEvaluationComponent;
  let fixture: ComponentFixture<PromptEvaluationComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PromptEvaluationComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PromptEvaluationComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
