"use strict";(self["webpackChunkfrontend"]=self["webpackChunkfrontend"]||[]).push([[723],{9723:function(e,a,t){t.r(a),t.d(a,{default:function(){return F}});var l=t(6768),s=t(4232),o=t(5130);const i={class:"motivation-container"},r={class:"employee-list"},n=["onClick"],m=["src"],u={class:"card-header"},d=["onClick"],c={class:"team-name"},p={class:"disc-type"},h={key:0,class:"factors"},k={class:"column"},f={class:"column"},y={class:"form-group"},v=["value"],L={class:"form-group"},b=["disabled"],g={key:0,class:"result-block"},C=["innerHTML"];function _(e,a,t,_,E,x){return(0,l.uX)(),(0,l.CE)("div",i,[a[22]||(a[22]=(0,l.Lk)("h1",null,"🎯 Мотивация сотрудника",-1)),(0,l.Lk)("div",r,[((0,l.uX)(!0),(0,l.CE)(l.FK,null,(0,l.pI)(E.employees,(e=>((0,l.uX)(),(0,l.CE)("div",{key:e.id,class:"employee-card",onClick:a=>x.selectEmployee(e)},[(0,l.Lk)("img",{class:"avatar",src:x.getAvatarUrl(e.ai_analysis),alt:"avatar",onError:a[0]||(a[0]=(...e)=>x.setDefaultAvatar&&x.setDefaultAvatar(...e))},null,40,m),(0,l.Lk)("div",u,[(0,l.Lk)("h4",null,(0,s.v_)(e.name),1),(0,l.Lk)("button",{onClick:(0,o.D$)((a=>x.deleteEmployee(e.id)),["stop"])},"🗑",8,d)]),(0,l.Lk)("p",c,"Команда: "+(0,s.v_)(x.getTeamName(e.team_id)||"—"),1),(0,l.Lk)("span",p,(0,s.v_)(x.extractDISCType(e.ai_analysis)),1),e.ai_analysis?((0,l.uX)(),(0,l.CE)("div",h,[(0,l.Lk)("div",k,[a[10]||(a[10]=(0,l.Lk)("h5",null,"⬆️ Мотивирующие",-1)),(0,l.Lk)("ul",null,[((0,l.uX)(!0),(0,l.CE)(l.FK,null,(0,l.pI)(e.motivators,(e=>((0,l.uX)(),(0,l.CE)("li",{key:e},(0,s.v_)(e),1)))),128))])]),(0,l.Lk)("div",f,[a[11]||(a[11]=(0,l.Lk)("h5",null,"⬇️ Демотиваторы",-1)),(0,l.Lk)("ul",null,[((0,l.uX)(!0),(0,l.CE)(l.FK,null,(0,l.pI)(e.demotivators,(e=>((0,l.uX)(),(0,l.CE)("li",{key:e},(0,s.v_)(e),1)))),128))])])])):(0,l.Q3)("",!0)],8,n)))),128)),(0,l.Lk)("div",{class:"employee-card add-card",onClick:a[1]||(a[1]=(...e)=>x.resetForm&&x.resetForm(...e))},a[12]||(a[12]=[(0,l.Lk)("span",null,"➕",-1),(0,l.Lk)("p",null,"Создать",-1)]))]),(0,l.Lk)("form",{onSubmit:a[9]||(a[9]=(0,o.D$)(((...e)=>x.submitMotivation&&x.submitMotivation(...e)),["prevent"]))},[(0,l.Lk)("div",y,[a[14]||(a[14]=(0,l.Lk)("label",null,"Имя сотрудника:",-1)),(0,l.bo)((0,l.Lk)("input",{"onUpdate:modelValue":a[2]||(a[2]=e=>E.form.name=e),placeholder:"Например: Иван Иванов",required:""},null,512),[[o.Jo,E.form.name]]),a[15]||(a[15]=(0,l.Lk)("label",null,"Должность:",-1)),(0,l.bo)((0,l.Lk)("input",{"onUpdate:modelValue":a[3]||(a[3]=e=>E.form.role=e),placeholder:"Аналитик, Разработчик...",required:""},null,512),[[o.Jo,E.form.role]]),a[16]||(a[16]=(0,l.Lk)("label",null,"Команда:",-1)),(0,l.bo)((0,l.Lk)("select",{"onUpdate:modelValue":a[4]||(a[4]=e=>E.form.team_id=e),required:""},[a[13]||(a[13]=(0,l.Lk)("option",{disabled:"",value:""},"Выберите команду",-1)),((0,l.uX)(!0),(0,l.CE)(l.FK,null,(0,l.pI)(E.teams,(e=>((0,l.uX)(),(0,l.CE)("option",{key:e.id,value:e.id},(0,s.v_)(e.name),9,v)))),128))],512),[[o.u1,E.form.team_id]])]),(0,l.Lk)("div",L,[a[17]||(a[17]=(0,l.Lk)("label",null,"1. Поведение в стрессовой ситуации",-1)),(0,l.bo)((0,l.Lk)("textarea",{"onUpdate:modelValue":a[5]||(a[5]=e=>E.form.stress=e),placeholder:"Как он реагирует на давление, конфликты...",required:""},null,512),[[o.Jo,E.form.stress]]),a[18]||(a[18]=(0,l.Lk)("label",null,"2. Взаимодействие с другими",-1)),(0,l.bo)((0,l.Lk)("textarea",{"onUpdate:modelValue":a[6]||(a[6]=e=>E.form.communication=e),placeholder:"Открытый, сдержанный, командный игрок?",required:""},null,512),[[o.Jo,E.form.communication]]),a[19]||(a[19]=(0,l.Lk)("label",null,"3. Особенности в работе",-1)),(0,l.bo)((0,l.Lk)("textarea",{"onUpdate:modelValue":a[7]||(a[7]=e=>E.form.behavior=e),placeholder:"Подход к задачам, ответственность...",required:""},null,512),[[o.Jo,E.form.behavior]]),a[20]||(a[20]=(0,l.Lk)("label",null,"4. Реакции на критику и изменения",-1)),(0,l.bo)((0,l.Lk)("textarea",{"onUpdate:modelValue":a[8]||(a[8]=e=>E.form.feedback=e),placeholder:"Как принимает обратную связь...",required:""},null,512),[[o.Jo,E.form.feedback]])]),(0,l.Lk)("button",{type:"submit",disabled:E.loading},(0,s.v_)(E.loading?"Анализируем...":"Сохранить и получить рекомендации"),9,b)],32),E.result?((0,l.uX)(),(0,l.CE)("div",g,[a[21]||(a[21]=(0,l.Lk)("h2",null,"📋 Рекомендации",-1)),(0,l.Lk)("div",{class:"ai-analysis",innerHTML:E.result},null,8,C)])):(0,l.Q3)("",!0)])}t(4114),t(8111),t(2489),t(116),t(1701);var E={data(){return{form:{id:null,name:"",role:"",team_id:"",stress:"",communication:"",behavior:"",feedback:""},teams:[],employees:[],result:"",loading:!1}},async mounted(){const e=localStorage.getItem("token"),a=await fetch("/user_teams",{headers:{Authorization:`Bearer ${e}`}});this.teams=await a.json();const t=await fetch("/employees"),l=await t.json();this.employees=l.map((e=>({...e,motivators:this.extractFactors(e.ai_analysis,"Мотивирующие"),demotivators:this.extractFactors(e.ai_analysis,"Демотиваторы")})))},methods:{async submitMotivation(){this.loading=!0;try{const e=await fetch("/motivation",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(this.form)}),a=await e.json();if(e.ok){this.result=a.analysis,this.form.id=a.employee_id;const e={...this.form,id:a.employee_id,ai_analysis:a.analysis,motivators:this.extractFactors(a.analysis,"Мотивирующие"),demotivators:this.extractFactors(a.analysis,"Демотиваторы")},t=this.employees.findIndex((e=>e.id===a.employee_id));-1!==t?this.employees.splice(t,1,e):this.employees.push(e)}else alert(a.error)}catch(e){alert("Ошибка подключения")}finally{this.loading=!1}},resetForm(){this.form={id:null,name:"",role:"",team_id:"",stress:"",communication:"",behavior:"",feedback:""},this.result=""},async deleteEmployee(e){confirm("Удалить сотрудника?")&&(await fetch(`/employee/${e}`,{method:"DELETE"}),this.employees=this.employees.filter((a=>a.id!==e)))},selectEmployee(e){this.form={...e},this.result=e.ai_analysis},extractFactors(e,a){if(!e)return[];const t=e.match(new RegExp(`${a}.*?:`,"i"));if(!t)return[];const l=e.indexOf(t[0]),s=e.slice(l),o=/^(Мотивирующие|Демотиваторы|Рекомендации)/gim,i=[...s.matchAll(o)];let r=s.length;i.length>1&&(r=i[1].index);const n=s.slice(0,r);return n.split(/[-–•●]/).map((e=>e.trim())).filter((e=>e.length>5&&!e.startsWith(a)))},extractDISCType(e){const a=e?.match(/\*\*Тип DISC:\*\*\s*(.*?)(\*\*|$)/);return a?a[1].trim():"Неизвестно"},getTeamName(e){const a=this.teams.find((a=>a.id===e));return a?a.name:"—"},getAvatarUrl(e){const a=this.extractDISCType(e),t=a?.toLowerCase().split(" ")[0].replace(/[^\w]/g,"");return`/avatars/${t||"default"}.png`},setDefaultAvatar(e){e.target.src="/avatars/default.png"}}},x=t(1241);const w=(0,x.A)(E,[["render",_]]);var F=w}}]);
//# sourceMappingURL=723.833192f1.js.map