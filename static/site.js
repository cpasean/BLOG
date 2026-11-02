/* Financial Doctor — site behaviour
 * 1. Background music (audio file uploaded in the editor) with play/pause and volume, like the old Wix player
 * 2. Page changes without reloading, so the music keeps playing
 */
(function () {
  "use strict";
  var box = document.getElementById("music");
  var OFF_KEY = "music-off", VOL_KEY = "music-vol";

  function sget(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }
  function sset(k, v) { try { v == null ? sessionStorage.removeItem(k) : sessionStorage.setItem(k, v); } catch (e) {} }

  /* ---------- music ---------- */
  if (box) {
    var btn = document.getElementById("music-btn");
    var vol = document.getElementById("music-vol");
    var audio = new Audio(box.getAttribute("data-src"));
    audio.loop = true;
    audio.preload = "auto";
    var v0 = parseFloat(sget(VOL_KEY));
    if (!isNaN(v0)) vol.value = v0;
    audio.volume = +vol.value;

    function setUI() {
      var on = !audio.paused;
      box.toggleAttribute("data-playing", on);
      btn.setAttribute("aria-label", on ? "Pause music" : "Play music");
    }
    audio.addEventListener("play", setUI);
    audio.addEventListener("pause", setUI);

    function start() {
      var pr = audio.play();
      if (pr && pr.catch) pr.catch(function () { /* blocked until the visitor interacts */ });
    }

    btn.addEventListener("click", function () {
      if (!audio.paused) { audio.pause(); sset(OFF_KEY, "1"); }   // visitor turned music off for this visit
      else { sset(OFF_KEY, null); start(); }
    });
    vol.addEventListener("input", function () { audio.volume = +vol.value; sset(VOL_KEY, vol.value); });

    // Try to play as soon as the site opens; if the browser blocks it, start on the first click, tap or key press
    if (!sget(OFF_KEY)) start();
    function firstTouch(e) {
      if (e.target.closest && e.target.closest("#music")) return;
      if (!audio.paused || sget(OFF_KEY)) return;
      start();
    }
    ["pointerdown", "keydown", "touchend"].forEach(function (ev) {
      document.addEventListener(ev, firstTouch, true);
    });
  }

  /* ---------- featured slider ---------- */
  function initSliders() {
    document.querySelectorAll("[data-slider]").forEach(function (s) {
      if (s.__ready) return; s.__ready = true;
      var track = s.querySelector(".track");
      function go(dir) {
        var w = track.clientWidth, max = track.scrollWidth - w;
        var x = track.scrollLeft + dir * w;
        if (x > max + 5) x = 0; else if (x < -5) x = max;   // loop around
        track.scrollTo({ left: x, behavior: "smooth" });
      }
      s.querySelector(".prev").addEventListener("click", function () { go(-1); });
      s.querySelector(".next").addEventListener("click", function () { go(1); });
    });
  }

  /* ---------- live view counts (Wix views + GoatCounter visits) ---------- */
  var gcMeta = document.querySelector('meta[name="gc"]');
  var gc = gcMeta && gcMeta.content;
  var viewCache = {};
  function initViews() {
    if (!gc) return;
    document.querySelectorAll(".vc[data-slug]").forEach(function (el) {
      var path = "/post/" + el.getAttribute("data-slug") + "/";
      var base = +el.getAttribute("data-base") || 0;
      var p = viewCache[path] || (viewCache[path] = fetch("https://" + gc + ".goatcounter.com/counter/" + encodeURIComponent(path) + ".json")
        .then(function (r) { return r.ok ? r.json() : { count: "0" }; })
        .then(function (j) { return parseInt(String(j.count).replace(/[^0-9]/g, ""), 10) || 0; })
        .catch(function () { return 0; }));
      p.then(function (n) { el.textContent = String(base + n); });
    });
  }
  function countVisit() {
    if (!gc) return;
    if (window.goatcounter && window.goatcounter.count) { window.goatcounter.count({ path: location.pathname }); return; }
    if (document.querySelector('script[data-goatcounter]')) return;
    var s = document.createElement("script");
    s.async = true; s.src = "https://gc.zgo.at/count.js";
    s.setAttribute("data-goatcounter", "https://" + gc + ".goatcounter.com/count");
    document.head.appendChild(s);
  }
  initSliders(); initViews(); countVisit();
  document.addEventListener("page:changed", function () { initSliders(); initViews(); countVisit(); });

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
      for (var i = 0; i < old.attributes.length; i++) s.setAttribute(old.attributes[i].name, old.attributes[i].value);
      if (!old.src) s.textContent = old.textContent;
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
