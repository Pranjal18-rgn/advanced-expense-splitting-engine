const API="http://127.0.0.1:5000";
let chartInstance;

// NAVIGATION
function showPage(p){
 document.querySelectorAll('.page').forEach(x=>x.style.display='none');
 document.getElementById(p).style.display='block';

 if(p==="expense") loadUsers();
}

// LOAD USERS
async function loadUsers(){
 let r=await fetch(API+'/users');
 let d=await r.json();

 payer.innerHTML='';

 d.forEach(u=>{
  let o=document.createElement('option');
  o.value=u.toLowerCase();
  o.text=u;
  payer.appendChild(o);
 });
}

// ADD USER
async function addUser(){
 if(!user.value) return alert("Enter name");

 await fetch(API+'/add_user',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({name:user.value})
 });

 user.value="";
 loadUsers();
}

// SPLIT TYPE TOGGLE
splitType.onchange=()=>{
 customBox.style.display =
  splitType.value==="custom" ? "block" : "none";
}

// ADD EXPENSE
async function addExpense(){

 if(!payer.value || !amount.value || !participants.value){
  alert("Fill all fields");
  return;
 }

 let parts = participants.value
  .split(',')
  .map(x=>x.trim().toLowerCase());

 let type = splitType.value;
 let splits = [];

 if(type==="custom"){
  customData.value.split(',').forEach(x=>{
   let [u,a]=x.split(':');
   splits.push({
    user:u.trim(),
    amount:+a
   });
  });
 }

 await fetch(API+'/add_expense',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({
   payer:payer.value,
   amount:+amount.value,
   participants:parts,
   type:type,
   splits:splits
  })
 });

 alert("Expense Added ✅");

 // clear fields
 participants.value="";
 amount.value="";
 customData.value="";
}

// BALANCES (FINAL CLEAN VERSION)
async function getBalances(){
 let r=await fetch(API+'/balances');
 let d=await r.json();

 balances.innerHTML='';

 Object.entries(d).forEach(([u,v])=>{

  // ✅ THIS IS THE FIX (REMOVES RAM, RIYA, etc.)
  if(v === 0) return;

  let li=document.createElement('li');

  if(v > 0){
    li.innerText=`🟢 ${u.toUpperCase()} gets ₹${v}`;
    li.style.color="green";
  }
  else{
    li.innerText=`🔴 ${u.toUpperCase()} owes ₹${Math.abs(v)}`;
    li.style.color="red";
  }

  balances.appendChild(li);
 });

 drawChart(d);
}

// SETTLE
async function settle(){
 let r=await fetch(API+'/settle');
 let d=await r.json();

 result.innerHTML='';

 d.forEach(x=>{
  let li=document.createElement('li');
  li.innerText=`${x.from} pays ${x.to} ₹${x.amount}`;
  result.appendChild(li);
 });
}

// HISTORY
async function history(){
 let r=await fetch(API+'/history');
 let d=await r.json();

 historyList.innerHTML='';

 d.forEach(x=>{
  let li=document.createElement('li');
  li.innerText=`${x[0]} paid ₹${x[1]} (${x[2]})`;
  historyList.appendChild(li);
 });
}

// RESET SESSION
async function resetAll(){
 await fetch(API+'/reset',{method:'POST'});

 alert("New session started ✅");

 balances.innerHTML='';
 result.innerHTML='';
 historyList.innerHTML='';

 loadUsers();
}

// GRAPH
function drawChart(data){
 if(chartInstance) chartInstance.destroy();

 chartInstance=new Chart(chart,{
  type:'bar',
  data:{
   labels:Object.keys(data),
   datasets:[{
    label:"Balances",
    data:Object.values(data)
   }]
  }
 });
}

// INIT
window.onload=loadUsers;
