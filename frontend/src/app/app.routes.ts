import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { AuthPage } from './pages/auth-page';
import { AgentPage } from './pages/agent-page';
import { LandingPage } from './pages/landing-page';
import { HomePage } from './pages/home-page';

export const routes: Routes = [
  { path: '', component: LandingPage, title: 'Idara — La Tunisie, simplifiée' },
  { path: 'home', component: HomePage, title: 'Idara — إدارة' },
  { path: 'login', component: AuthPage, title: 'Idara — Login' },
  { path: 'register', component: AuthPage, title: 'Idara — Register' },
  { path: 'assistant', canActivate: [authGuard], component: AgentPage, data: { assistant: true }, title: 'Idara — Assistant' },
  { path: 'agent/:slug', canActivate: [authGuard], component: AgentPage },
  { path: '**', redirectTo: '' },
];
