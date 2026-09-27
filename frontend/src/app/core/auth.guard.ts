import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth } from './auth.service';

export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(Auth);
  return auth.loggedIn() ? true : inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
};
