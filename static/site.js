/* Financial Doctor — site behaviour
 * 1. Background music (official Spotify player) that starts when a menu is clicked
 * 2. Page changes without reloading, so the music keeps playing (like the old Wix site)
 */
(function () {
  "use strict";
  var box = document.getElementById("music");
  var OFF_KEY = "music-off";
  var controller = null, wantPlay = false, playing = false;

  function store(get, val) {
    try { return get ? sessionStorage.getItem(OFF_KEY) : (val ? sessionStorage.setItem(OFF_KEY, "1") : sessionStorage.removeItem(OFF_KEY)); }
    catch (e) { return null; }
  }

  /* ---------- music ---------- */
  if (box) {
    var btn = document.getElementById("music-btn");
    var frame = box.querySelector(".frame");
    var label = btn.querySelector(".lbl");
    var uri = box.getAttribute("data-uri");

    function setUI() {
      box.toggleAttribute("data-open", !frame.hidden);
      box.toggleAttribute("data-playing", playing);
      btn.setAttribute("aria-expanded", String(!frame.hidden));
      btn.setAttribute("aria-label", playing ? "Pause music" : "Play music");
      label.textContent = playing ? "Pause" : "Music";
    }

    window.onSpotifyIframeApiReady = function (api) {
      var host = document.createElement("div");
      frame.appendChild(host);
      api.createController(host, { uri: uri, width: "100%", height: 80 }, function (c) {
        controller = c;
        c.addListener("playback_update", function (e) {
          playing = !e.data.isPaused;
          setUI();
        });
        if (wantPlay) c.play();
      });
    };
    var s = document.createElement("script");
    s.src = "https://open.spotify.com/embed/iframe-api/v1";
    s.async = true;
    document.head.appendChild(s);

    function start() {
      frame.hidden = false;
      wantPlay = true;
      if (controller) controller.play();
      setUI();
    }

    btn.addEventListener("click", function () {
      if (playing) {
        if (controller) controller.pause();
        store(false, true);           // visitor turned music off: stop auto-play for this visit
        frame.hidden = true;
      } else {
        store(false, false);
        start();
      }
      setUI();
    });

    // Auto-play when a menu item is clicked (a click lets the browser allow sound)
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest(".nav a, .panel a, .brand");
      if (!a || playing || store(true)) return;
      start();
    }, true);
    window.__startMusic = start;
  }

  /* ---------- page changes without reload ---------- */
  var main = document.querySelector("main");
  if (!main || !window.fetch || !window.history.pushState) return;

  function sameSitePage(a) {
    if (!a || a.target || a.hasAttribute("download") || a.origin !== location.origin) return false;
    var p = a.pathname;
    if (/\.(xml|xsl|mp4|jpe?g|png|gif|pdf|txt)$/i.test(p)) return false;
    if (p === location.pathname && a.hash) return false; // in-page anchor
    return true;
  }

  function runScripts(scope) {
    scope.querySelectorAll("script").forEach(function (old) {
      var s = document.createElement("script");
      if (old.src) s.src = old.src; else s.textContent = old.textContent;
      old.replaceWith(s);
    });
  }

  function swap(url, push) {
    return fetch(url, { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (html) {
      var doc = new DOMParser().parseFromString(html, "text/html");
      var newMain = doc.querySelector("main");
      // Pages that need extra libraries (math) load normally
      if (!newMain || doc.querySelector('script[src*="katex"]')) { location.href = url; return; }
      if (push) history.pushState({}, "", url);
      document.title = doc.title;
      var nav = doc.querySelector(".nav"), curNav = document.querySelector(".nav");
      if (nav && curNav) curNav.innerHTML = nav.innerHTML;
      var st = doc.querySelector("head style"), curSt = document.querySelector("head style");
      if (st && curSt && st.textContent !== curSt.textContent) curSt.textContent = st.textContent;
      main.innerHTML = newMain.innerHTML;
      runScripts(main);
      var target = location.hash && document.getElementById(location.hash.slice(1));
      if (target) target.scrollIntoView(); else window.scrollTo(0, 0);
      document.dispatchEvent(new Event("page:changed"));
    }).catch(function () { location.href = url; });
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest && e.target.closest("a[href]");
    if (!sameSitePage(a)) return;
    e.preventDefault();
    swap(a.href, true);
  });

  window.addEventListener("popstate", function () { swap(location.href, false); });
})();
