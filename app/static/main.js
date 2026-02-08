// =====================
// Helpers UI
// =====================

function showMessage(type, text) {
  // type: "success" | "danger" | "warning" | "info"
  const area = document.getElementById("message-area");
  area.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
          ${text}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>`;
}

function setButtonLoading(btn, isLoading, labelWhenDone = null) {
  if (!btn) return;
  if (isLoading) {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
      <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
      Attendere...
    `;
  } else {
    btn.disabled = false;
    btn.innerHTML = labelWhenDone ?? btn.dataset.originalHtml ?? "OK";
    delete btn.dataset.originalHtml;
  }
}

function setRowCheckboxesDisabled(disabled) {
  document
    .querySelectorAll('#list input.row-select[type="checkbox"]')
    .forEach(cb => cb.disabled = disabled);
  const selectAll = document.getElementById("select-all");
  if (selectAll) selectAll.disabled = disabled;
}

function setListLoading(loading) {
  const el = document.getElementById("list-loading");
  if (!el) return;
  el.style.display = loading ? "block" : "none";
}

function updateDeleteSelectedButtonState() {
  const checked = document.querySelectorAll(
    '#list input.row-select[type="checkbox"]:checked'
  );
  const btn = document.getElementById("delete-selected-btn");
  if (!btn) return;
  btn.disabled = checked.length === 0;
}

function wireSelectionHandlers() {
  const selectAll = document.getElementById("select-all");
  const rowCheckboxes = document.querySelectorAll(
    '#list input.row-select[type="checkbox"]'
  );

  if (selectAll) {
    selectAll.addEventListener("change", () => {
      rowCheckboxes.forEach((cb) => {
        cb.checked = selectAll.checked;
      });
      updateDeleteSelectedButtonState();
    });
  }

  rowCheckboxes.forEach((cb) => {
    cb.addEventListener("change", () => {
      updateDeleteSelectedButtonState();

      // Aggiorna stato select-all (checked se tutte selezionate, indeterminate se parziale)
      const total = rowCheckboxes.length;
      const checked = document.querySelectorAll(
        '#list input.row-select[type="checkbox"]:checked'
      ).length;
      if (selectAll) {
        selectAll.checked = checked === total && total > 0;
        selectAll.indeterminate = checked > 0 && checked < total;
      }
    });
  });

  // Stato iniziale
  if (selectAll) {
    const total = rowCheckboxes.length;
    const checked = document.querySelectorAll(
      '#list input.row-select[type="checkbox"]:checked'
    ).length;
    selectAll.checked = checked === total && total > 0;
    selectAll.indeterminate = checked > 0 && checked < total;
  }

  updateDeleteSelectedButtonState();
}

function escapeHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function buildURLFromPorts(ports) {
  try {
    if (!ports) return "";
    const keys = Object.keys(ports);
    if (keys.length === 0) return "";
    const firstKey = keys[0];
    const mapping = ports[firstKey];
    if (!Array.isArray(mapping) || mapping.length === 0) return "";
    const hostPort = mapping[0].HostPort;
    if (!hostPort) return "";
    return `http://localhost:${hostPort}`;
  } catch {
    return "";
  }
}

// =====================
// API Calls
// =====================

async function createContainers() {
  const countField = document.getElementById("count");
  const createBtn = document.getElementById("create-btn");
  const count = parseInt(countField.value);

  try {
    setButtonLoading(createBtn, true);

    const res = await fetch("/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ count }),
    });

    const data = await res.json();

    if (data.error) {
      showMessage("danger", data.error);
    } else {
      showMessage(
        "success",
        "Container creati: " + escapeHtml(JSON.stringify(data.created))
      );
      await loadList();
    }
  } catch (e) {
    showMessage("danger", "Errore durante la creazione dei container.");
  } finally {
    setButtonLoading(createBtn, false);
  }
}

async function loadList() {
  const container = document.getElementById("list");
  if (!container) return;

  setListLoading(true);
  container.innerHTML = "";

  try {
    const res = await fetch("/list");
    const list = await res.json();

    if (!Array.isArray(list) || list.length === 0) {
      container.innerHTML = `<p class="text-muted">Nessun container attivo.</p>`;
      updateDeleteSelectedButtonState();
      return;
    }

    let html = `
      <table class="table table-striped align-middle">
        <thead>
          <tr>
            <th style="width: 36px;">
              <input type="checkbox" id="select-all" title="Seleziona tutti" />
            </th>
            <th>Nome</th>
            <th>Stato</th>
            <!--<th>Porte</th>-->
            <th>URL</th>
            <th class="text-end col-actions"></th>
          </tr>
        </thead>
        <tbody>
    `;

    list.forEach((c) => {
      const url = c.url || buildURLFromPorts(c.ports);

      html += `
        <tr>
          <td>
            <input type="checkbox" class="row-select" data-id="${c.id}" title="Seleziona container ${escapeHtml(c.name)}"/>
          </td>
          <td>${escapeHtml(c.name)}</td>
          <td>${escapeHtml(c.status || "")}</td>
          <!--<td><code>${escapeHtml(JSON.stringify(c.ports))}</code></td>-->
          <td>${
            url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>` : ""
          }</td>
          <td class="text-end col-actions">
            <button class="btn btn-danger btn-sm" data-action="delete-one" data-id="${c.id}">Elimina</button>
          </td>
        </tr>
      `;
    });

    html += "</tbody></table>";
    container.innerHTML = html;

    // Wire up checkbox logic
    wireSelectionHandlers();

    // Wire up delete buttons for each row
    container.querySelectorAll('button[data-action="delete-one"]').forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-id");
        await deleteContainer(id, btn);
      });
    });
  } catch (e) {
    showMessage("danger", "Errore nel caricamento della lista.");
  } finally {
    setListLoading(false);
  }
}

// DELETE singolo con feedback visivo sul bottone di riga
async function deleteContainer(id, rowButtonEl = null) {
  try {
    setButtonLoading(rowButtonEl, true);
    setRowCheckboxesDisabled(true);

    const res = await fetch("/delete", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: [id] }),
    });

    const data = await res.json();

    if (data.removed && data.removed.length > 0) {
      showMessage("warning", "Container eliminato: " + escapeHtml(id));
    } else if (data.error) {
      showMessage("danger", escapeHtml(data.error));
    } else {
      showMessage("danger", "Errore nell'eliminazione del container");
    }
  } catch (e) {
    showMessage("danger", "Errore di rete durante l'eliminazione.");
  } finally {
    setButtonLoading(rowButtonEl, false);
    setRowCheckboxesDisabled(false);
    await loadList();
  }
}

// DELETE selezionati con spinner sul pulsante globale
async function deleteSelected() {
  const checked = Array.from(
    document.querySelectorAll('#list input.row-select[type="checkbox"]:checked')
  );
  if (checked.length === 0) {
    showMessage("info", "Nessun container selezionato.");
    return;
  }

  const ids = checked.map(cb => cb.getAttribute("data-id"));
  const bulkBtn = document.getElementById("delete-selected-btn");

  try {
    setButtonLoading(bulkBtn, true);
    setRowCheckboxesDisabled(true);
    setListLoading(true);

    const res = await fetch("/delete", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    });

    const data = await res.json();

    if (data.removed && data.removed.length > 0) {
      showMessage(
        "warning",
        `Eliminati ${data.removed.length} container selezionati.`
      );
    } else if (data.error) {
      showMessage("danger", escapeHtml(data.error));
    } else {
      showMessage("danger", "Errore nell'eliminazione dei container selezionati");
    }
  } catch (e) {
    showMessage("danger", "Errore di rete durante l'eliminazione selettiva.");
  } finally {
    setButtonLoading(bulkBtn, false);
    setRowCheckboxesDisabled(false);
    setListLoading(false);
    await loadList();
  }
}

// =====================
// Event wiring
// =====================

document.addEventListener("DOMContentLoaded", () => {
  // Carica la lista all'avvio
  loadList();

  // Bottoni principali
  const createBtn = document.getElementById("create-btn");
  if (createBtn) createBtn.addEventListener("click", createContainers);

  const refreshBtn = document.getElementById("refresh-btn");
  if (refreshBtn) refreshBtn.addEventListener("click", loadList);

  const deleteSelectedBtn = document.getElementById("delete-selected-btn");
  if (deleteSelectedBtn) deleteSelectedBtn.addEventListener("click", deleteSelected);
});