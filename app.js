/* KU TRUCK ＆ TYRE SERVICE — shared interactions
   Works on both the homepage and the service detail pages.
   Every lookup is guarded, so elements absent on a given page are skipped. */
(function () {
  'use strict';

  // ── Loader: hide shortly after window load ──────────────────────────
  window.addEventListener('load', function () {
    var loader = document.getElementById('loader');
    if (loader) setTimeout(function () { loader.classList.add('hide'); }, 800);
  });

  // ── Scroll effects: sticky-nav state, hero parallax, sticker drift ──
  var nav = document.getElementById('nav');
  var heroBg = document.getElementById('heroBg');
  var stickers = document.querySelectorAll('.hero-stickers .sk');
  var heroSpeed = document.querySelector('.hero') ? 0.4 : 0.35; // subpages scroll a touch slower
  var stickerSpeeds = [0.5, 0.7, 0.6, 0.8];
  var stickerRot = [-6, 5, -3, 8];

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      var y = window.scrollY;
      if (nav) nav.classList.toggle('scr', y > 40);
      if (heroBg) heroBg.style.transform = 'translate3d(0,' + (y * heroSpeed) + 'px,0) scale(1.1)';
      for (var i = 0; i < stickers.length; i++) {
        var sp = stickerSpeeds[i] || 0.6;
        stickers[i].style.transform = 'translateY(' + (y * -sp) + 'px) rotate(' + (stickerRot[i] || 0) + 'deg)';
      }
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  // ── Mobile menu drawer ──────────────────────────────────────────────
  var burger = document.getElementById('burger');
  var menu = document.getElementById('menu');
  if (burger && menu) {
    var scrim = document.createElement('div');
    scrim.className = 'nav-scrim';
    document.body.appendChild(scrim);

    function setOpen(open) {
      menu.classList.toggle('open', open);
      scrim.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    }
    burger.addEventListener('click', function () {
      setOpen(!menu.classList.contains('open'));
    });
    scrim.addEventListener('click', function () { setOpen(false); });
    // Close after tapping a link, and on Escape
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { setOpen(false); });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
  }
})();
