import { ComponentFixture, TestBed } from '@angular/core/testing';

import { IterationAnalysisComponent } from './iteration-analysis.component';

describe('IterationAnalysisComponent', () => {
  let component: IterationAnalysisComponent;
  let fixture: ComponentFixture<IterationAnalysisComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IterationAnalysisComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(IterationAnalysisComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
