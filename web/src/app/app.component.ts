import { Component } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { provideHttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [],
  providers: [provideHttpClient()],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  apiBase = '/api';
  username = '';
  principals = '';
  ttl = '8h';
  pubkey = '';
  result = '';
  serial: number | null = null;

  constructor(private http: HttpClient) {}

  sign() {
    const body = {
      username: this.username.trim(),
      principals: this.principals.split(',').map(s => s.trim()).filter(Boolean),
      pubkey: this.pubkey.trim(),
      ttl: this.ttl.trim() || '8h'
    };
    const headers = new HttpHeaders({'Content-Type':'application/json'});
    this.http.post<any>(`${this.apiBase}/api/v1/sign`, body, { headers })
      .subscribe({
        next: r => {
          this.result = r.cert;
          this.serial = r.serial;
        },
        error: err => {
          alert('Sign error: ' + (err.error?.detail || err.message));
        }
      });
  }

  downloadCert() {
    if (!this.result) return;
    const blob = new Blob([this.result + "\n"], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'id_ed25519-cert.pub';
    a.click();
    URL.revokeObjectURL(a.href);
  }
}
