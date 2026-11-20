import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { APOLLO_OPTIONS, ApolloModule } from 'apollo-angular';
import { HttpLink } from 'apollo-angular/http';
import { InMemoryCache } from '@apollo/client/core';

import { environment } from '../environments/environment';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { DashboardPlaceholderComponent } from './dashboard-placeholder/dashboard-placeholder.component';
import { AuthInterceptor } from './interceptors/auth.interceptor';
import { LoginComponent } from './login/login.component';

export function createApollo(httpLink: HttpLink) {
  return {
    link: httpLink.create({ uri: environment.graphqlUrl }),
    cache: new InMemoryCache(),
  };
}

@NgModule({
  declarations: [AppComponent, LoginComponent, DashboardPlaceholderComponent],
  imports: [BrowserModule, HttpClientModule, FormsModule, ApolloModule, AppRoutingModule],
  providers: [
    { provide: APOLLO_OPTIONS, useFactory: createApollo, deps: [HttpLink] },
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
