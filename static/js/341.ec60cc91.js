"use strict";(self["webpackChunkfrontend"]=self["webpackChunkfrontend"]||[]).push([[341],{3341:function(e,o,l){l.r(o),l.d(o,{default:function(){return L}});var a=l(6768),t=l(4232),n=l(5130);const r={class:"motivation-container"},i={class:"form-group"},s=["value"],d={class:"form-group"},m=["value"],u={class:"form-group"},c=["disabled"],p={key:0,class:"result-block"},f=["innerHTML"];function b(e,o,l,b,k,h){return(0,a.uX)(),(0,a.CE)("div",r,[o[22]||(o[22]=(0,a.Lk)("h1",null,"🎯 Мотивация сотрудника",-1)),(0,a.Lk)("div",i,[o[12]||(o[12]=(0,a.Lk)("label",null,"Выберите сотрудника:",-1)),(0,a.bo)((0,a.Lk)("select",{"onUpdate:modelValue":o[0]||(o[0]=e=>k.selectedEmployeeId=e),onChange:o[1]||(o[1]=(...e)=>h.loadEmployeeData&&h.loadEmployeeData(...e))},[o[11]||(o[11]=(0,a.Lk)("option",{disabled:"",value:""},"— Создать нового —",-1)),((0,a.uX)(!0),(0,a.CE)(a.FK,null,(0,a.pI)(k.employees,(e=>((0,a.uX)(),(0,a.CE)("option",{key:e.id,value:e.id},(0,t.v_)(e.name)+" — "+(0,t.v_)(e.role),9,s)))),128))],544),[[n.u1,k.selectedEmployeeId]])]),(0,a.Lk)("form",{onSubmit:o[9]||(o[9]=(0,n.D$)(((...e)=>h.submitMotivation&&h.submitMotivation(...e)),["prevent"]))},[(0,a.Lk)("div",d,[o[14]||(o[14]=(0,a.Lk)("label",null,"Имя сотрудника:",-1)),(0,a.bo)((0,a.Lk)("input",{"onUpdate:modelValue":o[2]||(o[2]=e=>k.form.name=e),placeholder:"Например: Иван Иванов",required:""},null,512),[[n.Jo,k.form.name]]),o[15]||(o[15]=(0,a.Lk)("label",null,"Должность:",-1)),(0,a.bo)((0,a.Lk)("input",{"onUpdate:modelValue":o[3]||(o[3]=e=>k.form.role=e),placeholder:"Например: Аналитик, Разработчик...",required:""},null,512),[[n.Jo,k.form.role]]),o[16]||(o[16]=(0,a.Lk)("label",null,"Команда:",-1)),(0,a.bo)((0,a.Lk)("select",{"onUpdate:modelValue":o[4]||(o[4]=e=>k.form.team_id=e),required:""},[o[13]||(o[13]=(0,a.Lk)("option",{disabled:"",value:""},"Выберите команду",-1)),((0,a.uX)(!0),(0,a.CE)(a.FK,null,(0,a.pI)(k.teams,(e=>((0,a.uX)(),(0,a.CE)("option",{key:e.id,value:e.id},(0,t.v_)(e.name),9,m)))),128))],512),[[n.u1,k.form.team_id]])]),(0,a.Lk)("div",u,[o[17]||(o[17]=(0,a.Lk)("label",null,"1. Поведение в стрессовой ситуации",-1)),(0,a.bo)((0,a.Lk)("textarea",{"onUpdate:modelValue":o[5]||(o[5]=e=>k.form.stress=e),placeholder:"Как он реагирует на давление, конфликты...",required:""},null,512),[[n.Jo,k.form.stress]]),o[18]||(o[18]=(0,a.Lk)("label",null,"2. Взаимодействие с другими",-1)),(0,a.bo)((0,a.Lk)("textarea",{"onUpdate:modelValue":o[6]||(o[6]=e=>k.form.communication=e),placeholder:"Открытый, сдержанный, любит работать в команде или один...",required:""},null,512),[[n.Jo,k.form.communication]]),o[19]||(o[19]=(0,a.Lk)("label",null,"3. Особенности в работе",-1)),(0,a.bo)((0,a.Lk)("textarea",{"onUpdate:modelValue":o[7]||(o[7]=e=>k.form.behavior=e),placeholder:"Привычки, подход, структура, планирование...",required:""},null,512),[[n.Jo,k.form.behavior]]),o[20]||(o[20]=(0,a.Lk)("label",null,"4. Реакции на критику и изменения",-1)),(0,a.bo)((0,a.Lk)("textarea",{"onUpdate:modelValue":o[8]||(o[8]=e=>k.form.feedback=e),placeholder:"Как принимает фидбек, открыт к переменам...",required:""},null,512),[[n.Jo,k.form.feedback]])]),(0,a.Lk)("button",{type:"submit",disabled:k.loading},(0,t.v_)(k.loading?"Сохраняем и анализируем...":"Сохранить и получить рекомендации"),9,c)],32),k.result?((0,a.uX)(),(0,a.CE)("div",p,[o[21]||(o[21]=(0,a.Lk)("h2",null,"📋 Рекомендации",-1)),(0,a.Lk)("div",{innerHTML:k.result},null,8,f),(0,a.Lk)("button",{onClick:o[10]||(o[10]=(...e)=>h.resetForm&&h.resetForm(...e))},"Новый сотрудник")])):(0,a.Q3)("",!0)])}var k={data(){return{form:{name:"",role:"",team_id:"",stress:"",communication:"",behavior:"",feedback:""},selectedEmployeeId:"",teams:[],employees:[],result:"",loading:!1}},async mounted(){const e=await fetch("/teams"),o=await fetch("/employees");this.teams=(await e.json()).teams,this.employees=await o.json()},methods:{async loadEmployeeData(){if(!this.selectedEmployeeId)return this.resetForm();const e=await fetch(`/employee/${this.selectedEmployeeId}`),o=await e.json();this.form={name:o.name,role:o.role,team_id:o.team_id,stress:o.stress,communication:o.communication,behavior:o.behavior,feedback:o.feedback},this.result=o.ai_analysis||""},async submitMotivation(){this.loading=!0;try{const e=await fetch("/motivation",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(this.form)}),o=await e.json();e.ok?this.result=o.result:alert(o.error)}catch(e){alert("Ошибка подключения")}finally{this.loading=!1}},resetForm(){this.selectedEmployeeId="",this.form={name:"",role:"",team_id:"",stress:"",communication:"",behavior:"",feedback:""},this.result=""}}},h=l(1241);const v=(0,h.A)(k,[["render",b],["__scopeId","data-v-189fd5d8"]]);var L=v}}]);
//# sourceMappingURL=341.ec60cc91.js.map