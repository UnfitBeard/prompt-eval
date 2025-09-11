import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminTemplateCreatorComponent } from './admin-template-creator.component';

describe('AdminTemplateCreatorComponent', () => {
  let component: AdminTemplateCreatorComponent;
  let fixture: ComponentFixture<AdminTemplateCreatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminTemplateCreatorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AdminTemplateCreatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
