import { ProductionCountPipe } from './production-count.pipe';
describe('ProductionCountPipe',()=>{it('counts production versions',()=>{const models:any=[{versions:[{stage:'PRODUCTION'},{stage:'STAGING'}]}];expect(new ProductionCountPipe().transform(models)).toBe(1)})});
