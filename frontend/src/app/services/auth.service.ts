import { Injectable } from '@angular/core';
import { Apollo, gql } from 'apollo-angular';
import { map, Observable, tap } from 'rxjs';

export interface SignedInUser {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'resident';
  flatId: number | null;
}

interface LoginPayload {
  success: boolean;
  message: string;
  accessToken: string | null;
  user: SignedInUser | null;
}

interface LoginMutation {
  login: LoginPayload;
}

const LOGIN_MUTATION = gql`
  mutation Login($email: String!, $password: String!) {
    login(email: $email, password: $password) {
      success
      message
      accessToken
      user { id name email role flatId }
    }
  }
`;

const TOKEN_KEY = 'society-doom-token';
const USER_KEY = 'society-doom-user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  constructor(private readonly apollo: Apollo) {}

  login(email: string, password: string): Observable<LoginPayload> {
    return this.apollo.mutate<LoginMutation>({
      mutation: LOGIN_MUTATION,
      variables: { email, password },
      fetchPolicy: 'no-cache',
    }).pipe(
      map((result) => {
        if (!result.data?.login) throw new Error('The server did not return a login result.');
        return result.data.login;
      }),
      tap((result) => {
        if (result.success && result.accessToken && result.user) {
          localStorage.setItem(TOKEN_KEY, result.accessToken);
          localStorage.setItem(USER_KEY, JSON.stringify(result.user));
        }
      }),
    );
  }

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  get currentUser(): SignedInUser | null {
    const rawUser = localStorage.getItem(USER_KEY);
    if (!rawUser) return null;
    try {
      return JSON.parse(rawUser) as SignedInUser;
    } catch {
      this.logout();
      return null;
    }
  }

  get isAuthenticated(): boolean {
    return Boolean(this.token && this.currentUser);
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}
