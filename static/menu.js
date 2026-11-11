// Keep the native button toggle; dismiss the menu on any other page click.
const menu = document.querySelector('.live-menu');
const menuButton = menu?.querySelector('summary');
if (menu && menuButton) {
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
    const scrolled = window.scrollY > 60;
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
