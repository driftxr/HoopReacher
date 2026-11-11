// Keep the native button toggle; dismiss the menu on any other page click.
const menu = document.querySelector('.live-menu');
const menuButton = menu?.querySelector('summary');
if (menu && menuButton) {
  const syncMenuState = () => menuButton.setAttribute('aria-expanded', String(menu.open));
  menu.addEventListener('toggle', syncMenuState);
  syncMenuState();
  document.addEventListener('click', (event) => {
    if (menu.open && !menuButton.contains(event.target)) menu.open = false;
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu.open) {
      menu.open = false;
      menuButton.focus();
    }
  });
}

// Swap the top ribbon for the circular menu after leaving the top of the page.
const ribbon = document.querySelector('.site-ribbon');
if (ribbon && menu) {
  let previous;
  const syncNavigation = () => {
    const scrolled = window.scrollY > 0;
    if (scrolled === previous) return;
    previous = scrolled;
    const focused = document.activeElement;
    document.body.classList.toggle('navigation-scrolled', scrolled);
    ribbon.inert = scrolled;
    ribbon.setAttribute('aria-hidden', String(scrolled));
    menu.inert = !scrolled;
    menu.setAttribute('aria-hidden', String(!scrolled));
    if (!scrolled) menu.open = false;
    if (scrolled && ribbon.contains(focused)) menuButton.focus({preventScroll:true});
    if (!scrolled && menu.contains(focused)) ribbon.querySelector('.site-brand').focus({preventScroll:true});
  };
  window.addEventListener('scroll', syncNavigation, {passive:true});
  window.addEventListener('pageshow', syncNavigation);
  syncNavigation();
}

// Highlight the current section on both generated pages and Python routes.
const pagePath = location.pathname.split('/').pop() || 'index.html';
const originPage = new URLSearchParams(location.search).get('back');
const section = /^(today|game)([.-]|$)/.test(pagePath) ? 'today' : /^standings/.test(pagePath) || (/^team/.test(pagePath) && originPage === 'standings') ? 'standings' : 'home';
for (const link of document.querySelectorAll('.site-ribbon nav a,.live-nav a')) {
  const destination = new URL(link.href).pathname.split('/').pop();
  const target = /^standings/.test(destination) ? 'standings' : /^today/.test(destination) ? 'today' : 'home';
  if (target === section) link.setAttribute('aria-current','page');
  else link.removeAttribute('aria-current');
}
