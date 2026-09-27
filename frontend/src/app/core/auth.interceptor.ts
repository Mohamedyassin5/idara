import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Auth } from './auth.service';

/** Adds the JWT to every /api call and signs the user out when the server rejects the token. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(Auth);
  const token = auth.token();
  const isAuthCall = req.url.startsWith('/api/auth/login') || req.url.startsWith('/api/auth/register');
  const authed = token && req.url.startsWith('/api') ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
  return next(authed).pipe(
    catchError((err: unknown) => {
      if (err instanceof HttpErrorResponse && err.status === 401 && !isAuthCall && token) auth.logout();
      return throwError(() => err);
    }),
  );
};
