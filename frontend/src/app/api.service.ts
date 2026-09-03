import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Deployment, Metrics, Model } from './types';
@Injectable({providedIn:'root'}) export class ApiService {
  private readonly http=inject(HttpClient); private readonly base='/api';
  models(q=''):Observable<Model[]>{return this.http.get<Model[]>(`${this.base}/models`,{params:q?{q}:{}})}
  deployments():Observable<Deployment[]>{return this.http.get<Deployment[]>(`${this.base}/deployments`)}
  metrics(id:string):Observable<Metrics>{return this.http.get<Metrics>(`${this.base}/models/${id}/metrics`)}
  retry(id:string):Observable<Deployment>{return this.http.post<Deployment>(`${this.base}/deployments/${id}/retry`,{})}
  rollback(id:string):Observable<Deployment>{return this.http.post<Deployment>(`${this.base}/deployments/${id}/rollback`,{})}
}
