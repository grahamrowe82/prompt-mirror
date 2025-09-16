(function () {
  function parseDataAttribute(value) {
    if (!value) return "";
    try {
      return JSON.parse(value);
    } catch (err) {
      return value;
    }
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderDiff(original, rewrite) {
    var container = document.getElementById("diff-output");
    if (!container) return;
    container.innerHTML = "";
    var originalLines = (original || "").split(/\r?\n/);
    var rewriteLines = (rewrite || "").split(/\r?\n/);
    var maxLen = Math.max(originalLines.length, rewriteLines.length);

    for (var i = 0; i < maxLen; i += 1) {
      var originalLine = originalLines[i] || "";
      var rewriteLine = rewriteLines[i] || "";
      if (originalLine === rewriteLine) {
        if (!originalLine) {
          continue;
        }
        var sameEl = document.createElement("span");
        sameEl.className = "diff-line same";
        sameEl.innerHTML = "  " + escapeHtml(originalLine);
        container.appendChild(sameEl);
        continue;
      }
      if (originalLine) {
        var removeEl = document.createElement("span");
        removeEl.className = "diff-line remove";
        removeEl.innerHTML = "- " + escapeHtml(originalLine);
        container.appendChild(removeEl);
      }
      if (rewriteLine) {
        var addEl = document.createElement("span");
        addEl.className = "diff-line add";
        addEl.innerHTML = "+ " + escapeHtml(rewriteLine);
        container.appendChild(addEl);
      }
    }

    if (!container.children.length) {
      var emptyEl = document.createElement("span");
      emptyEl.className = "diff-line same";
      emptyEl.textContent = "No diff to display.";
      container.appendChild(emptyEl);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var select = document.getElementById("preset-select");
    var textarea = document.getElementById("prompt_text");
    var preview = document.getElementById("preset-preview");
    var previewBody = document.getElementById("preset-preview-body");

    if (select && textarea) {
      select.addEventListener("change", function () {
        var option = select.options[select.selectedIndex];
        if (!option) return;
        var rawPrompt = parseDataAttribute(option.dataset.rough);
        var goodPrompt = parseDataAttribute(option.dataset.good);
        if (rawPrompt) {
          textarea.value = rawPrompt;
          textarea.dispatchEvent(new Event("input"));
        }
        if (goodPrompt && preview && previewBody) {
          preview.hidden = false;
          previewBody.textContent = goodPrompt;
        } else if (preview) {
          preview.hidden = true;
          if (previewBody) previewBody.textContent = "";
        }
      });
    }

    var copyButton = document.getElementById("copy-button");
    if (copyButton) {
      copyButton.addEventListener("click", function () {
        var targetId = copyButton.getAttribute("data-target");
        if (!targetId) return;
        var target = document.getElementById(targetId);
        if (!target) return;
        var text = target.textContent || "";
        if (!navigator.clipboard || !navigator.clipboard.writeText) {
          copyButton.textContent = "Copy not available";
          setTimeout(function () {
            copyButton.textContent = "Copy rewrite";
          }, 1600);
          return;
        }

        navigator.clipboard
          .writeText(text)
          .then(function () {
            var originalLabel = copyButton.textContent;
            copyButton.textContent = "Copied!";
            setTimeout(function () {
              copyButton.textContent = originalLabel;
            }, 1600);
          })
          .catch(function () {
            copyButton.textContent = "Copy not available";
            setTimeout(function () {
              copyButton.textContent = "Copy rewrite";
            }, 1600);
          });
      });
    }

    var diffDataScript = document.getElementById("diff-data");
    if (diffDataScript) {
      try {
        var payload = JSON.parse(diffDataScript.textContent || "{}");
        renderDiff(payload.original || "", payload.rewrite || "");
      } catch (err) {
        console.error("Prompt Mirror diff parse error", err);
      }
    }
  });
})();
