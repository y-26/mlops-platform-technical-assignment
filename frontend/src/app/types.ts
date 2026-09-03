export interface Version {id:number;model_id:string;version:string;framework:string;algorithm:string;artifact_uri:string;training_data_ref:string;approval_status:string;stage:string;created_at:string}
export interface Model {id:string;name:string;description:string;owner:string;tags:Record<string,string>;versions:Version[];updated_at:string}
export interface Event {id:number;status:string;event:string;detail:string|null;created_at:string}
export interface Deployment {id:string;model_id:string;environment:string;status:string;attempt:number;failure_reason:string|null;created_at:string;events:Event[];version:Version}
export interface Metric {timestamp:string;version:string;latency_ms:number;throughput_rpm:number;error_rate:number;quality_score:number;drift_score:number;availability:number}
export interface Metrics {items:Metric[];monitoring_status:string;last_successful_inference:string|null}
