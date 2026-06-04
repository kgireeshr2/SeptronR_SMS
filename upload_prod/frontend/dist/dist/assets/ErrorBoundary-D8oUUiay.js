import{c as t}from"./createLucideIcon-BIFp25O1.js";import{R as o,j as r}from"./index-Dh40l2XQ.js";import{C as a}from"./circle-alert-Lhhst4LZ.js";import{R as n}from"./refresh-cw-_i8Uy8mA.js";/**
 * @license lucide-react v0.383.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const l=t("LogOut",[["path",{d:"M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4",key:"1uf3rs"}],["polyline",{points:"16 17 21 12 16 7",key:"1gabdz"}],["line",{x1:"21",x2:"9",y1:"12",y2:"12",key:"1uyos4"}]]);/**
 * @license lucide-react v0.383.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const p=t("Moon",[["path",{d:"M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z",key:"a7tn18"}]]);/**
 * @license lucide-react v0.383.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const x=t("Sun",[["circle",{cx:"12",cy:"12",r:"4",key:"4exip2"}],["path",{d:"M12 2v2",key:"tus03m"}],["path",{d:"M12 20v2",key:"1lh1kg"}],["path",{d:"m4.93 4.93 1.41 1.41",key:"149t6j"}],["path",{d:"m17.66 17.66 1.41 1.41",key:"ptbguv"}],["path",{d:"M2 12h2",key:"1t8f8n"}],["path",{d:"M20 12h2",key:"1q8mjw"}],["path",{d:"m6.34 17.66-1.41 1.41",key:"1m8zz5"}],["path",{d:"m19.07 4.93-1.41 1.41",key:"1shlcs"}]]);class u extends o.Component{constructor(e){super(e),this.state={hasError:!1}}static getDerivedStateFromError(e){return{hasError:!0,error:e}}componentDidCatch(e,s){console.error("[ErrorBoundary] Caught error:",e,s)}render(){var e;return this.state.hasError?r.jsxs("div",{className:"flex min-h-[400px] flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50 p-8",children:[r.jsx(a,{size:48,className:"text-red-400"}),r.jsxs("div",{className:"text-center",children:[r.jsx("h2",{className:"text-lg font-semibold text-red-800",children:"Something went wrong"}),r.jsx("p",{className:"mt-1 text-sm text-red-600",children:((e=this.state.error)==null?void 0:e.message)??"An unexpected error occurred."})]}),r.jsxs("button",{onClick:()=>this.setState({hasError:!1,error:void 0}),className:"flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700",children:[r.jsx(n,{size:14}),"Try Again"]})]}):this.props.children}}export{u as E,l as L,p as M,x as S};
