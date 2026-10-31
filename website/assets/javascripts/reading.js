/* Keep a linked answer visible when the target lives inside a disclosure. */
(() => {
  // Material uses labels to drive hidden checkbox/radio controls. Keep that
  // binding while making the visible controls reachable from the keyboard.
  const bindHeaderControls = () => {
    document.querySelectorAll("header label.md-header__button[for]").forEach(label => {
      const input = document.getElementById(label.htmlFor);
      if (!input) return;
      const names = { __drawer: "导航菜单", __search: "搜索" };
      const name = label.title || names[input.id];
      if (!name) return;
      label.tabIndex = 0;
      label.setAttribute("role", "button");
      label.setAttribute("aria-label", name);
      // Material handles Enter on keyup. Add Space without bubbling a second
      // activation to the theme, and suppress its default page scrolling.
      label.addEventListener("keydown", event => {
        if (event.key === " ") event.preventDefault();
      });
      label.addEventListener("keyup", event => {
        if (event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          label.click();
        }
      });
      if (input.type === "checkbox") {
        const update = () => label.setAttribute("aria-expanded", String(input.checked));
        input.addEventListener("change", update);
        update();
      }
    });
    document.addEventListener("keydown", event => {
      const drawer = document.getElementById("__drawer");
      if (event.key === "Escape" && drawer?.checked) {
        drawer.click();
        document.querySelector('header label[for="__drawer"]')?.focus();
      }
    });
  };

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

  const bindImagePreview = () => {
    const dialog = document.createElement("dialog");
    if (typeof dialog.showModal !== "function") return;
    dialog.className = "diagram-lightbox";
    dialog.setAttribute("aria-label", "图片放大预览");

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "diagram-lightbox__close";
    closeButton.setAttribute("aria-label", "关闭图片");
    closeButton.autofocus = true;
    closeButton.textContent = "×";

    const preview = document.createElement("img");
    dialog.append(closeButton, preview);
    document.body.append(dialog);
    let trigger;

    closeButton.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", event => {
      if (event.target === dialog || event.target === preview) dialog.close();
    });
    dialog.addEventListener("close", () => {
      document.documentElement.classList.remove("image-preview-open");
      preview.removeAttribute("src");
      trigger?.focus({ preventScroll: true });
    });

    document.querySelectorAll(".md-typeset a > img").forEach(image => {
      const link = image.parentElement;
      // Preserve ordinary linked images that lead somewhere other than the image.
      if (link.href !== image.src) return;
      link.classList.add("diagram-zoom");
      link.setAttribute("aria-haspopup", "dialog");
      link.setAttribute("aria-label", `放大图片：${image.alt || "插图"}`);
      link.addEventListener("click", event => {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        trigger = link;
        preview.src = image.currentSrc || image.src;
        preview.alt = image.alt;
        document.documentElement.classList.add("image-preview-open");
        dialog.showModal();
      });
    });
  };
  window.addEventListener("hashchange", revealTarget);
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      revealTarget();
      bindHeaderControls();
      bindImagePreview();
    });
  } else {
    revealTarget();
    bindHeaderControls();
    bindImagePreview();
  }
})();
