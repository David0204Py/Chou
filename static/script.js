// script.js
document.addEventListener('DOMContentLoaded', function() {
    var buttons = document.querySelectorAll('button');
 
    buttons.forEach(function(button) {
       button.addEventListener('click', function() {
          button.style.backgroundColor = '#000064';
          button.style.color = '#FFFFFF';
       });
    });
 });
 