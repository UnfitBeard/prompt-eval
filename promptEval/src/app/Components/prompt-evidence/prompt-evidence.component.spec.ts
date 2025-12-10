import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PromptEvidenceComponent } from './prompt-evidence.component';

describe('PromptEvidenceComponent', () => {
  let component: PromptEvidenceComponent;
  let fixture: ComponentFixture<PromptEvidenceComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PromptEvidenceComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PromptEvidenceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
