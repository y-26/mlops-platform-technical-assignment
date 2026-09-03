import { Pipe, PipeTransform } from '@angular/core'; import { Model } from './types';
@Pipe({name:'productionCount',standalone:true}) export class ProductionCountPipe implements PipeTransform {transform(models:Model[]):number{return models.flatMap(m=>m.versions).filter(v=>v.stage==='PRODUCTION').length}}
