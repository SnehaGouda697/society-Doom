import { Injectable } from '@angular/core';
import { Apollo, gql } from 'apollo-angular';
import { Observable, map } from 'rxjs';

export interface Bill {
  id: number;
  category: string;
  amount: number;
  units: number | null;
  status: string;
  dueDate: string;
}

export interface FlatReport {
  flatId: number;
  flatNo: string;
  month: number;
  year: number;
  score: number;
  badge: string;
  points: { cleanliness: number; discipline: number; events: number; total: number };
  bills: Bill[];
  totalBilled: number;
}

export interface SocietyReport {
  month: number;
  year: number;
  averageScore: number;
  flatCount: number;
  totalBilled: number;
  collected: number;
  pending: number;
  doomZoneCount: number;
}

export interface FlatSummary {
  flatId: number;
  flatNo: string;
  score: number;
  badge: string;
}

export interface UsagePoint { month: number; year: number; units: number }
export interface ActionResult { success: boolean; message: string; count: number }
export interface PropertyRecord { id: number; flatNo: string; block: string; type: string; areaSqft: number; residentCount: number; score: number; badge: string }
export interface TenantRecord { id: number; name: string; email: string; role: string; flatNo: string | null }
export interface FinanceBill { id: number; flatNo: string; category: string; amount: number; status: string; dueDate: string }
export interface MaintenanceRecord { id: number; flatId: number; flatNo: string; title: string; category: string; description: string; status: string; createdOn: string }

const FLAT_REPORT = gql`
  query FlatReport($flatId: Int!, $month: Int!, $year: Int!) {
    flatReport(flatId: $flatId, month: $month, year: $year) {
      flatId flatNo month year score badge totalBilled
      points { cleanliness discipline events total }
      bills { id category amount units status dueDate }
    }
  }
`;

const SOCIETY_REPORT = gql`
  query SocietyReport($month: Int!, $year: Int!) {
    societyReport(month: $month, year: $year) {
      month year averageScore flatCount totalBilled collected pending doomZoneCount
    }
  }
`;

const LEADERBOARD = gql`
  query Leaderboard($month: Int!, $year: Int!) {
    leaderboard(month: $month, year: $year) { flatId flatNo score badge }
  }
`;

const USAGE_TREND = gql`
  query UsageTrend($flatId: Int!, $category: String!, $months: Int!) {
    usageTrend(flatId: $flatId, category: $category, months: $months) { month year units }
  }
`;

const GENERATE_BILLS = gql`
  mutation GenerateBills($month: Int!, $year: Int!) {
    generateBills(month: $month, year: $year) { success message count }
  }
`;

const ADD_POINTS = gql`
  mutation AddPoints($flatId: Int!, $category: String!, $points: Int!, $note: String!, $month: Int!, $year: Int!) {
    addPoints(flatId: $flatId, category: $category, points: $points, note: $note, month: $month, year: $year) { success message count }
  }
`;

const ADD_METER_READING = gql`
  mutation AddMeterReading($flatId: Int!, $month: Int!, $year: Int!, $category: String!, $units: Float!) {
    addMeterReading(flatId: $flatId, month: $month, year: $year, category: $category, units: $units) { success message count }
  }
`;

const LOG_GYM = gql`
  mutation LogGym($flatId: Int!, $visitDate: Date!, $minutes: Int!) {
    logGym(flatId: $flatId, visitDate: $visitDate, minutes: $minutes) { success message count }
  }
`;

const MARK_BILL_PAID = gql`
  mutation MarkBillPaid($billId: Int!) {
    markBillPaid(billId: $billId) { success message count }
  }
`;

const PROPERTIES = gql`
  query Properties($month: Int!, $year: Int!) {
    properties(month: $month, year: $year) { id flatNo block type areaSqft residentCount score badge }
  }
`;

const TENANTS = gql`
  query Tenants { tenants { id name email role flatNo } }
`;

const FINANCE_BILLS = gql`
  query FinanceBills($month: Int!, $year: Int!) {
    financeBills(month: $month, year: $year) { id flatNo category amount status dueDate }
  }
`;

const MAINTENANCE_REQUESTS = gql`
  query MaintenanceRequests { maintenanceRequests { id flatId flatNo title category description status createdOn } }
`;

const CREATE_MAINTENANCE_REQUEST = gql`
  mutation CreateMaintenanceRequest($title: String!, $category: String!, $description: String!, $flatId: Int) {
    createMaintenanceRequest(title: $title, category: $category, description: $description, flatId: $flatId) { success message count }
  }
`;

const UPDATE_MAINTENANCE_STATUS = gql`
  mutation UpdateMaintenanceStatus($requestId: Int!, $status: String!) {
    updateMaintenanceStatus(requestId: $requestId, status: $status) { success message count }
  }
`;

@Injectable({ providedIn: 'root' })
export class DashboardService {
  constructor(private readonly apollo: Apollo) {}

  flatReport(flatId: number, month: number, year: number): Observable<FlatReport | null> {
    return this.apollo.query<{ flatReport: FlatReport | null }>({
      query: FLAT_REPORT, variables: { flatId, month, year }, fetchPolicy: 'network-only',
    }).pipe(map((result) => result.data.flatReport));
  }

  societyReport(month: number, year: number): Observable<SocietyReport> {
    return this.apollo.query<{ societyReport: SocietyReport }>({
      query: SOCIETY_REPORT, variables: { month, year }, fetchPolicy: 'network-only',
    }).pipe(map((result) => result.data.societyReport));
  }

  leaderboard(month: number, year: number): Observable<FlatSummary[]> {
    return this.apollo.query<{ leaderboard: FlatSummary[] }>({
      query: LEADERBOARD, variables: { month, year }, fetchPolicy: 'network-only',
    }).pipe(map((result) => result.data.leaderboard));
  }

  usageTrend(flatId: number, category: string): Observable<UsagePoint[]> {
    return this.apollo.query<{ usageTrend: UsagePoint[] }>({
      query: USAGE_TREND, variables: { flatId, category, months: 6 }, fetchPolicy: 'network-only',
    }).pipe(map((result) => result.data.usageTrend));
  }

  generateBills(month: number, year: number): Observable<ActionResult> {
    return this.mutate(GENERATE_BILLS, { month, year }, 'generateBills');
  }

  addPoints(input: { flatId: number; category: string; points: number; note: string; month: number; year: number }): Observable<ActionResult> {
    return this.mutate(ADD_POINTS, input, 'addPoints');
  }

  addMeterReading(input: { flatId: number; month: number; year: number; category: string; units: number }): Observable<ActionResult> {
    return this.mutate(ADD_METER_READING, input, 'addMeterReading');
  }

  logGym(input: { flatId: number; visitDate: string; minutes: number }): Observable<ActionResult> {
    return this.mutate(LOG_GYM, input, 'logGym');
  }

  markBillPaid(billId: number): Observable<ActionResult> {
    return this.mutate(MARK_BILL_PAID, { billId }, 'markBillPaid');
  }

  properties(month: number, year: number): Observable<PropertyRecord[]> {
    return this.apollo.query<{ properties: PropertyRecord[] }>({ query: PROPERTIES, variables: { month, year }, fetchPolicy: 'network-only' })
      .pipe(map((result) => result.data.properties));
  }

  tenants(): Observable<TenantRecord[]> {
    return this.apollo.query<{ tenants: TenantRecord[] }>({ query: TENANTS, fetchPolicy: 'network-only' })
      .pipe(map((result) => result.data.tenants));
  }

  financeBills(month: number, year: number): Observable<FinanceBill[]> {
    return this.apollo.query<{ financeBills: FinanceBill[] }>({ query: FINANCE_BILLS, variables: { month, year }, fetchPolicy: 'network-only' })
      .pipe(map((result) => result.data.financeBills));
  }

  maintenanceRequests(): Observable<MaintenanceRecord[]> {
    return this.apollo.query<{ maintenanceRequests: MaintenanceRecord[] }>({ query: MAINTENANCE_REQUESTS, fetchPolicy: 'network-only' })
      .pipe(map((result) => result.data.maintenanceRequests));
  }

  createMaintenanceRequest(input: { title: string; category: string; description: string; flatId: number | null }): Observable<ActionResult> {
    return this.mutate(CREATE_MAINTENANCE_REQUEST, input, 'createMaintenanceRequest');
  }

  updateMaintenanceStatus(requestId: number, status: string): Observable<ActionResult> {
    return this.mutate(UPDATE_MAINTENANCE_STATUS, { requestId, status }, 'updateMaintenanceStatus');
  }

  private mutate<T>(mutation: any, variables: object, key: string): Observable<T> {
    return this.apollo.mutate<Record<string, T>>({ mutation, variables }).pipe(
      map((result) => {
        const value = result.data?.[key];
        if (!value) throw new Error('The server did not return an action result.');
        return value;
      }),
    );
  }
}
