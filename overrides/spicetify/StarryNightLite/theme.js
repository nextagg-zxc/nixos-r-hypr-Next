function waitForElement(els, func, timeout = 100) {
  const queries = els.map((el) => document.querySelector(el));
  if (queries.every((a) => a)) {
    func(queries);
  } else if (timeout > 0) {
    setTimeout(waitForElement, 300, els, func, --timeout);
  }
}

function random(min, max) {
  // min inclusive max exclusive
  return Math.random() * (max - min) + min;
}

waitForElement(['.Root__top-container'], ([topContainer]) => {
  const r = document.documentElement;
  const rs = window.getComputedStyle(r);

  const backgroundContainer = document.createElement('div');
  backgroundContainer.className = 'starrynight-bg-container';
  topContainer.appendChild(backgroundContainer);

  // to position stars and shooting stars between the background and everything else
  const rootElement = document.querySelector('.Root__top-container');
  rootElement.style.zIndex = '0';

  // StarryNight Lite: static stars painted once on a single canvas,
  // a few twinkling stars animated via opacity only (compositor, no repaint)
  const sky = document.createElement('canvas');
  sky.className = 'starrynight-sky';
  backgroundContainer.appendChild(sky);

  const starColor = rs.getPropertyValue('--spice-star').trim() || '#fff';
  let skyKey = '';
  const paintSky = () => {
    const dpr = window.devicePixelRatio || 1;
    const w = backgroundContainer.clientWidth;
    const h = backgroundContainer.clientHeight;
    const key = `${w}x${h}@${dpr}`;
    if (!w || !h || key === skyKey) return;
    skyKey = key;
    sky.width = Math.round(w * dpr);
    sky.height = Math.round(h * dpr);
    const ctx = sky.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.fillStyle = starColor;
    const count = (w * h) / 4000;
    for (let i = 0; i < count; i++) {
      const size = Math.random() < 0.5 ? 1 : 2;
      ctx.globalAlpha = random(0.5, 1);
      ctx.beginPath();
      ctx.arc(random(0, 0.99) * w, random(0, 0.99) * h, size / 2, 0, Math.PI * 2);
      ctx.fill();
    }
  };
  paintSky();
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(paintSky, 250);
  });

  for (let i = 0; i < 40; i++) {
    const star = document.createElement('div');
    star.className = 'starrynight-twinkle';
    star.style.left = `${random(0, 99)}%`;
    star.style.top = `${random(0, 99)}%`;
    star.style.animationDelay = `${-random(0, 5).toFixed(2)}s`;
    backgroundContainer.appendChild(star);
  }

  // Pause only when the window is really not visible. Hyprland's hidden
  // workspaces keep document.hidden false but stop delivering frames, so
  // probe with a single rAF once a second (no permanent rAF loop).
  const setPaused = (p) => r.classList.toggle('starrynight-paused', p);
  setInterval(() => {
    if (document.hidden) return setPaused(true);
    let drawn = false;
    requestAnimationFrame(() => { drawn = true; setPaused(false); });
    setTimeout(() => { if (!drawn) setPaused(true); }, 700);
  }, 1000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) setPaused(false);
  });

  // handles resizing of playbar panel to match right sidebar below it
  const playbar = document.querySelector('.Root__now-playing-bar');
  waitForElement(['.Root__right-sidebar'], ([rightbar]) => {
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === rightbar) {
          let newWidth = entry.contentRect.width;
          if (newWidth === 0) {
            const localStorageWidth = localStorage.getItem(
              '223ni6f2epqcidhx5etjafeai:panel-width-saved'
            );
            if (localStorageWidth) {
              newWidth = localStorageWidth;
            } else {
              newWidth = 420;
            }
          }
          playbar.style.width = `${newWidth}px`;
          break;
        }
      }
    });

    resizeObserver.observe(rightbar);
  });

  /*
  Pure CSS Shooting Star Animation Effect Copyright (c) 2021 by Delroy Prithvi (https://codepen.io/delroyprithvi/pen/LYyJROR)

  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
  */
  for (let i = 0; i < 4; i++) {
    const shootingstar = document.createElement('span');
    shootingstar.className = 'shootingstar';
    if (Math.random() < 0.75) {
      shootingstar.style.top = '-4px'; // hidden off screen when animation is delayed
      shootingstar.style.right = `${random(0, 90)}%`;
    } else {
      shootingstar.style.top = `${random(0, 50)}%`;
      shootingstar.style.right = '-4px'; // hidden when animation is delayed
    }

    const shootingStarGlowColor = `rgba(${rs.getPropertyValue(
      '--spice-rgb-shooting-star-glow'
    )},${0.1})`;
    shootingstar.style.boxShadow = `0 0 0 4px ${shootingStarGlowColor}, 0 0 0 8px ${shootingStarGlowColor}, 0 0 20px ${shootingStarGlowColor}`;

    shootingstar.style.animationDuration = `${
      Math.floor(Math.random() * 3) + 3
    }s`;
    shootingstar.style.animationDelay = `${Math.floor(Math.random() * 7)}s`;

    backgroundContainer.appendChild(shootingstar);

    shootingstar.addEventListener('animationend', () => {
      if (Math.random() < 0.75) {
        shootingstar.style.top = '-4px'; // hidden off screen when animation is delayed
        shootingstar.style.right = `${random(0, 90)}%`;
      } else {
        shootingstar.style.top = `${random(0, 50)}%`;
        shootingstar.style.right = '-4px'; // hidden when animation is delayed
      }

      shootingstar.style.animation = 'none'; // Remove animation

      void shootingstar.offsetWidth;

      shootingstar.style.animation = '';
      shootingstar.style.setProperty("animation-duration", `${Math.floor(Math.random() * 4) + 3}s`, "important");
    });
  }
});
