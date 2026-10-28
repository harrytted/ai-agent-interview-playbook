/* Keep a linked answer visible when the target lives inside a disclosure. */
(() => {
  const revealTarget = () => {
    if (!location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    let parent = target.parentElement;
    let opened = false;
    while (parent) {
      if (parent.tagName === "DETAILS" && !parent.open) {
        parent.open = true;
        opened = true;
      }
      parent = parent.parentElement;
    }
    if (opened) requestAnimationFrame(() => target.scrollIntoView());
  };
  window.addEventListener("hashchange", revealTarget);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", revealTarget);
  } else {
    revealTarget();
  }
})();
