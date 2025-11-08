// === Shortcuts ===
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

// === Sidebar Toggle ===
$("#sidebarToggle").onclick = () => $(".sidebar").classList.toggle("horizontal");



let cont = document.querySelector(".container_1");    

function Object1(number , type){
for(let i = 0; i < number; i++ ){
let element = document.createElement("div");
element.className = `object ${type}`;
cont.appendChild(element);

let x = Math.random() * window.innerWidth ;
let y = Math.random() * window.innerHeight ;
let speedX = (Math.random() - 0.5) * 4;
let speedY = (Math.random() - 0.5) *4;

function bouncing(){
x += speedX;
y += speedY;
if(x <= 0 || x >= window.innerWidth - 50) speedX = -speedX;
if(y <= 0 || y >= window.innerHeight -50) speedY = -speedY;

element.style.transform =`translate(${x}px, ${y}px)`;

requestAnimationFrame(bouncing)
}
bouncing();

}

}
Object1(45,"square");


(function (){
      let date= new Date();
      document.querySelector('.timer').innerHTML=date.toDateString();})();
       let content = document.querySelector(".compact-content-wrapper_resource");
        content = content.innerHTML;

        let holder = document.querySelector(".study-main");

        holder.innerHTML =content;

        let content2 = document.getElementById("announcement-content");
        let holder2 = document.getElementById("announcementsList")
        holder2.innerHTML = content2.innerHTML;

        function verifyLogout(){
let option = document.querySelector(".v-logout");
        option.style.display = "block"


        }
        function stay_login(){
        let option = document.querySelector(".v-logout");
        option.style.display = "none"
}

function editPic(){
let save = document.getElementById("saveButton");
let cancel = document.getElementById("cancelButton");
save.style.display ="block";
cancel.style.display = "block";
}
function hideButton(){
let save = document.getElementById("saveButton");
let cancel = document.getElementById("cancelButton");
save.style.display ="none";
cancel.style.display = "none";

}






