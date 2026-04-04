/* main.js — Хроники России */

// Mobile nav toggle
const burger = document.getElementById('navBurger');
const links  = document.getElementById('navLinks');

if (burger && links) {
  burger.addEventListener('click', () => {
    links.classList.toggle('open');
  });
}

// Auto-dismiss messages
document.querySelectorAll('.message').forEach((msg) => {
  setTimeout(() => {
    msg.style.opacity = '0';
    msg.style.transform = 'translateX(30px)';
    msg.style.transition = 'all .4s';
    setTimeout(() => msg.remove(), 400);
  }, 4000);
});
