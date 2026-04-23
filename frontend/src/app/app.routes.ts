import { Routes } from '@angular/router';
import { RegisterComponent } from './pages/register.component';
import { GamePageComponent } from './pages/game-page/game-page.component';

export const routes: Routes = [
  { path: '', component: GamePageComponent },
  { path: 'game', component: GamePageComponent },
  { path: 'register', component: RegisterComponent },

];