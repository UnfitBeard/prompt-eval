import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PrompterProfileComponent } from './prompter-profile.component';

describe('PrompterProfileComponent', () => {
  let component: PrompterProfileComponent;
  let fixture: ComponentFixture<PrompterProfileComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PrompterProfileComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PrompterProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
