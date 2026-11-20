import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { ActionResult, DashboardService, FinanceBill, FlatReport, FlatSummary, MaintenanceRecord, PropertyRecord, SocietyReport, TenantRecord, UsagePoint } from '../services/dashboard.service';

@Component({
  selector: 'sd-dashboard',
  templateUrl: './dashboard-placeholder.component.html',
  styleUrls: ['./dashboard-placeholder.component.scss'],
})
export class DashboardPlaceholderComponent implements OnInit {
  readonly monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  readonly years = Array.from({ length: 5 }, (_, index) => new Date().getFullYear() - 2 + index);
  month = new Date().getMonth() + 1;
  year = new Date().getFullYear();
  report: SocietyReport | null = null;
  flatReport: FlatReport | null = null;
  leaderboard: FlatSummary[] = [];
  electricity: UsagePoint[] = [];
  water: UsagePoint[] = [];
  loading = true;
  sectionLoading = false;
  actionBusy = false;
  errorMessage = '';
  notice = '';
  sectionError = '';
  activeSection = 'dashboard';
  readonly navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: '▦' },
    { id: 'properties', label: 'Properties', icon: '▤' },
    { id: 'finance', label: 'Finance', icon: '◉' },
    { id: 'tenants', label: 'Tenants', icon: '♙' },
    { id: 'maintenance', label: 'Maintenance', icon: '⌁' },
    { id: 'settings', label: 'Settings', icon: '⚙' },
  ];
  properties: PropertyRecord[] = [];
  tenants: TenantRecord[] = [];
  financeBills: FinanceBill[] = [];
  scoreTrend: Array<{ label: string; score: number }> = [];
  maintenanceRequests: MaintenanceRecord[] = [];
  maintenanceFlatOptions: PropertyRecord[] = [];
  maintenanceTitle = '';
  maintenanceCategory = 'plumbing';
  maintenanceDescription = '';
  maintenanceFlatId: number | null = null;

  pointsFlatId = 0;
  pointsCategory = 'cleanliness';
  pointsValue = 5;
  pointsNote = '';
  readingFlatId = 0;
  readingCategory = 'electricity';
  readingUnits = 0;
  gymFlatId = 0;
  gymDate = this.todayInput();
  gymMinutes = 30;

  constructor(
    public readonly auth: AuthService,
    private readonly dashboard: DashboardService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadDashboard();
  }

  get isAdmin(): boolean { return this.auth.currentUser?.role === 'admin'; }
  get flats(): FlatSummary[] { return this.leaderboard; }
  get topFlats(): FlatSummary[] { return this.leaderboard.slice(0, 5); }
  get pendingBills(): number { return this.flatReport?.bills.filter((bill) => bill.status !== 'paid').length ?? 0; }
  get paidBills(): number { return this.flatReport?.bills.filter((bill) => bill.status === 'paid').length ?? 0; }
  get residentRank(): number { return this.leaderboard.findIndex((item) => item.flatId === this.flatReport?.flatId); }
  get pageTitle(): string { return this.navigation.find((item) => item.id === this.activeSection)?.label ?? 'Dashboard'; }
  get collectedAmount(): number { return this.financeBills.filter((bill) => bill.status === 'paid').reduce((total, bill) => total + bill.amount, 0); }
  get pendingAmount(): number { return this.financeBills.filter((bill) => bill.status !== 'paid').reduce((total, bill) => total + bill.amount, 0); }
  get openMaintenanceCount(): number { return this.maintenanceRequests.filter((request) => request.status !== 'resolved').length; }
  get occupiedPropertyCount(): number { return this.properties.filter((property) => property.residentCount > 0).length; }
  get assignedTenantCount(): number { return this.tenants.filter((tenant) => Boolean(tenant.flatNo)).length; }
  get averagePropertyScore(): number {
    return this.properties.length ? this.properties.reduce((sum, property) => sum + property.score, 0) / this.properties.length : 0;
  }
  get overdueAmount(): number {
    const today = new Date().toISOString().slice(0, 10);
    return this.financeBills.filter((bill) => bill.status !== 'paid' && bill.dueDate < today)
      .reduce((total, bill) => total + bill.amount, 0);
  }
  get revenueGroups(): Array<{ category: string; amount: number; color: string }> {
    const colors: Record<string, string> = { electricity: '#08d9e8', water: '#ffd44f', maintenance: '#a56bff', clubhouse: '#5c789d', gym: '#24d68e' };
    const totals = new Map<string, number>();
    this.financeBills.forEach((bill) => totals.set(bill.category, (totals.get(bill.category) ?? 0) + bill.amount));
    return Array.from(totals.entries()).map(([category, amount]) => ({ category, amount, color: colors[category] ?? '#8da4c3' }))
      .sort((first, second) => second.amount - first.amount);
  }
  get revenueDonut(): string {
    const total = this.revenueGroups.reduce((sum, item) => sum + item.amount, 0);
    if (!total) return 'conic-gradient(#263a52 0 100%)';
    let start = 0;
    const stops = this.revenueGroups.map((item) => {
      const end = start + item.amount / total * 100;
      const stop = `${item.color} ${start.toFixed(2)}% ${end.toFixed(2)}%`;
      start = end;
      return stop;
    });
    return `conic-gradient(${stops.join(', ')})`;
  }
  get topRevenueHomes(): Array<{ flatNo: string; amount: number }> {
    const totals = new Map<string, number>();
    this.financeBills.forEach((bill) => totals.set(bill.flatNo, (totals.get(bill.flatNo) ?? 0) + bill.amount));
    return Array.from(totals.entries()).map(([flatNo, amount]) => ({ flatNo, amount }))
      .sort((first, second) => second.amount - first.amount).slice(0, 5);
  }
  get trendPolyline(): string {
    return this.scoreTrend.map((item, index) => `${20 + index * 92},${126 - item.score}`).join(' ');
  }
  get trendArea(): string {
    const points = this.scoreTrend.map((item, index) => `${20 + index * 92},${126 - item.score}`);
    return points.length ? `M ${points[0]} L ${points.slice(1).join(' L ')} L 480,132 L 20,132 Z` : '';
  }
  get maxHomeRevenue(): number { return Math.max(...this.topRevenueHomes.map((home) => home.amount), 1); }

  loadDashboard(preserveNotice = false): void {
    this.loading = true;
    this.errorMessage = '';
    if (!preserveNotice) this.notice = '';
    const board$ = this.dashboard.leaderboard(this.month, this.year);

    if (this.isAdmin) {
      const periods = this.previousPeriods(6);
      forkJoin({
        report: this.dashboard.societyReport(this.month, this.year),
        leaderboard: board$,
        bills: this.dashboard.financeBills(this.month, this.year),
        properties: this.dashboard.properties(this.month, this.year),
        trend: forkJoin(periods.map((period) => this.dashboard.societyReport(period.month, period.year))),
      }).subscribe({
        next: ({ report, leaderboard, bills, properties, trend }) => {
          this.report = report;
          this.leaderboard = leaderboard;
          this.financeBills = bills;
          this.properties = properties;
          this.scoreTrend = trend.map((item, index) => ({ label: periods[index].label, score: item.averageScore }));
          this.loading = false;
          this.setDefaultFlat();
        },
        error: () => this.failLoad('Could not load society data. Check that the backend is running and try again.'),
      });
      return;
    }

    const flatId = this.auth.currentUser?.flatId;
    if (flatId == null) {
      this.failLoad('This resident account is not linked to a flat.');
      return;
    }
    forkJoin({
      report: this.dashboard.flatReport(flatId, this.month, this.year),
      leaderboard: board$,
      electricity: this.dashboard.usageTrend(flatId, 'electricity'),
      water: this.dashboard.usageTrend(flatId, 'water'),
    }).subscribe({
      next: ({ report, leaderboard, electricity, water }) => {
        this.flatReport = report;
        this.leaderboard = leaderboard;
        this.electricity = electricity;
        this.water = water;
        this.loading = false;
      },
      error: () => this.failLoad('Could not load your report. Check your connection and try again.'),
    });
  }

  setSection(section: string): void {
    this.activeSection = section;
    this.notice = '';
    this.sectionError = '';
    if (section !== 'dashboard') this.loadSection();
    if (section === 'dashboard') this.loadDashboard();
  }

  onPeriodChange(): void {
    if (this.activeSection === 'dashboard') this.loadDashboard();
    else if (this.activeSection !== 'settings') this.loadSection();
  }

  submitMaintenance(): void {
    this.runAction(this.dashboard.createMaintenanceRequest({
      title: this.maintenanceTitle.trim(), category: this.maintenanceCategory,
      description: this.maintenanceDescription.trim(), flatId: this.isAdmin ? this.maintenanceFlatId : null,
    }));
  }

  changeMaintenanceStatus(requestId: number, status: string): void {
    this.runAction(this.dashboard.updateMaintenanceStatus(requestId, status));
  }

  signOut(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }

  markPaid(billId: number): void {
    this.runAction(this.dashboard.markBillPaid(billId));
  }

  generateBills(): void {
    this.runAction(this.dashboard.generateBills(this.month, this.year));
  }

  savePoints(): void {
    this.runAction(this.dashboard.addPoints({
      flatId: Number(this.pointsFlatId), category: this.pointsCategory, points: Number(this.pointsValue),
      note: this.pointsNote.trim(), month: this.month, year: this.year,
    }));
  }

  saveReading(): void {
    this.runAction(this.dashboard.addMeterReading({
      flatId: Number(this.readingFlatId), month: this.month, year: this.year,
      category: this.readingCategory, units: Number(this.readingUnits),
    }));
  }

  saveGymLog(): void {
    this.runAction(this.dashboard.logGym({
      flatId: Number(this.gymFlatId), visitDate: this.gymDate, minutes: Number(this.gymMinutes),
    }));
  }

  currency(value: number): string {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
  }

  monthLabel(month: number, year: number): string { return `${this.monthNames[month - 1]} ${year}`; }
  categoryLabel(category: string): string { return category.replace(/_/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase()); }

  usageHeight(points: UsagePoint[], index: number): number {
    const max = Math.max(...points.map((point) => point.units), 1);
    return Math.max(8, Math.round((points[index].units / max) * 100));
  }

  private runAction(action: import('rxjs').Observable<ActionResult>): void {
    if (this.actionBusy) return;
    this.actionBusy = true;
    this.errorMessage = '';
    this.notice = '';
    action.subscribe({
      next: (result) => {
        this.actionBusy = false;
        if (!result.success) {
          this.errorMessage = result.message;
          return;
        }
        this.notice = result.message;
        this.maintenanceTitle = '';
        this.maintenanceDescription = '';
        if (this.activeSection === 'dashboard') this.loadDashboard(true);
        else this.loadSection(true);
      },
      error: (error: { graphQLErrors?: Array<{ message: string }>; message?: string }) => {
        this.actionBusy = false;
        this.errorMessage = error.graphQLErrors?.[0]?.message ?? error.message ?? 'That action could not be completed.';
      },
    });
  }

  private loadSection(preserveNotice = false): void {
    this.sectionLoading = true;
    this.sectionError = '';
    if (!preserveNotice) this.notice = '';
    if (this.activeSection === 'properties') {
      this.dashboard.properties(this.month, this.year).subscribe({ next: (items) => { this.properties = items; this.sectionLoading = false; }, error: () => this.failSection('Could not load properties.') });
    } else if (this.activeSection === 'finance') {
      this.dashboard.financeBills(this.month, this.year).subscribe({ next: (items) => { this.financeBills = items; this.sectionLoading = false; }, error: () => this.failSection('Could not load finance data.') });
    } else if (this.activeSection === 'tenants') {
      this.dashboard.tenants().subscribe({ next: (items) => { this.tenants = items; this.sectionLoading = false; }, error: () => this.failSection('Could not load tenant information.') });
    } else if (this.activeSection === 'maintenance') {
      this.dashboard.maintenanceRequests().subscribe({
        next: (items) => { this.maintenanceRequests = items; this.sectionLoading = false; },
        error: () => this.failSection('Could not load maintenance requests.'),
      });
      if (this.isAdmin) {
        this.dashboard.properties(this.month, this.year).subscribe({
          next: (items) => {
            this.maintenanceFlatOptions = items;
            if (this.maintenanceFlatId == null && items.length) this.maintenanceFlatId = items[0].id;
          },
          error: () => { this.sectionError = 'Could not load the home list.'; },
        });
      }
    } else if (this.activeSection === 'settings') {
      this.dashboard.properties(this.month, this.year).subscribe({
        next: (items) => { this.properties = items; this.sectionLoading = false; },
        error: () => this.failSection('Could not load your account details.'),
      });
    } else {
      this.sectionLoading = false;
    }
  }

  private failSection(message: string): void {
    this.sectionLoading = false;
    this.sectionError = message;
  }

  private failLoad(message: string): void {
    this.loading = false;
    this.errorMessage = message;
  }

  private setDefaultFlat(): void {
    const firstFlat = this.leaderboard[0]?.flatId ?? 0;
    if (this.pointsFlatId === 0) this.pointsFlatId = firstFlat;
    if (this.readingFlatId === 0) this.readingFlatId = firstFlat;
    if (this.gymFlatId === 0) this.gymFlatId = firstFlat;
  }

  private todayInput(): string {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  }

  private previousPeriods(count: number): Array<{ month: number; year: number; label: string }> {
    return Array.from({ length: count }, (_, index) => {
      const date = new Date(this.year, this.month - count + index, 1);
      return { month: date.getMonth() + 1, year: date.getFullYear(), label: this.monthNames[date.getMonth()].slice(0, 3) };
    });
  }
}
