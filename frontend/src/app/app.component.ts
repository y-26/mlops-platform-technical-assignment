import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { catchError, debounceTime, distinctUntilChanged, of, startWith, switchMap } from 'rxjs';
import { ApiService } from './api.service';
import { Deployment, Metric, Model } from './types';
import { ProductionCountPipe } from './production-count.pipe';
@Component({selector:'app-root',standalone:true,imports:[CommonModule,ReactiveFormsModule,ProductionCountPipe],templateUrl:'./app.component.html'})
export class AppComponent implements OnInit {
  private readonly api=inject(ApiService); search=new FormControl('',{nonNullable:true}); deploymentStatus=new FormControl('ALL',{nonNullable:true});
  models:Model[]=[]; deployments:Deployment[]=[]; metrics:Metric[]=[]; selected?:Model;
  loading=true; error=''; monitoringStatus='NO_DATA'; lastInference:string|null=null; toast='';
  ngOnInit(){this.search.valueChanges.pipe(startWith(''),debounceTime(250),distinctUntilChanged(),switchMap(q=>{this.loading=true;this.error='';return this.api.models(q).pipe(catchError(()=>{this.error='Could not load the model registry. Check that the API is healthy and retry.';return of([])}))})).subscribe(models=>{this.models=models;this.selected=models[0];this.loading=false;if(this.selected)this.loadMetrics(this.selected.id)});this.loadDeployments()}
  get filteredDeployments():Deployment[]{const status=this.deploymentStatus.value;return status==='ALL'?this.deployments:this.deployments.filter(d=>d.status===status)}
  get latestDeployment():Deployment|undefined{return this.deployments[0]}
  select(model:Model){this.selected=model;this.loadMetrics(model.id)}
  loadDeployments(){this.api.deployments().pipe(catchError(()=>of([]))).subscribe(items=>this.deployments=items)}
  loadMetrics(id:string){this.api.metrics(id).pipe(catchError(()=>of({items:[],monitoring_status:'ERROR',last_successful_inference:null}))).subscribe(result=>{this.metrics=result.items;this.monitoringStatus=result.monitoring_status;this.lastInference=result.last_successful_inference})}
  action(d:Deployment,kind:'retry'|'rollback'){const request=kind==='retry'?this.api.retry(d.id):this.api.rollback(d.id);request.subscribe({next:()=>{this.toast=`${kind==='retry'?'Retry':'Rollback'} completed`;this.loadDeployments()},error:e=>this.toast=e.error?.error?.message??'Operation failed'})}
  latest(key:keyof Metric):number{return this.metrics.length?Number(this.metrics[this.metrics.length-1][key]):0}
  height(metric:Metric):number{return Math.max(3,Math.min(100,metric.quality_score*100))}
  trackId(_:number,item:{id:string|number}){return item.id}
}
