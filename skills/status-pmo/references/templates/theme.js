// Alternador de tema claro/escuro. Sem o botão, vale o prefers-color-scheme
// do sistema; a escolha manual é gravada em localStorage e força data-theme.
(() => {
  "use strict";
  const STORAGE_KEY = "status-pmo-theme";
  const root = document.documentElement;

  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "dark" || saved === "light") root.dataset.theme = saved;

  const isDark = () =>
    root.dataset.theme === "dark" ||
    (!root.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);

  const button = document.createElement("button");
  button.type = "button";
  button.className = "theme-toggle";

  const paint = () => {
    button.textContent = isDark() ? "☀ Tema claro" : "☾ Tema escuro";
    button.setAttribute("aria-pressed", String(isDark()));
  };

  button.addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem(STORAGE_KEY, next);
    paint();
  });

  document.body.appendChild(button);
  paint();
})();
