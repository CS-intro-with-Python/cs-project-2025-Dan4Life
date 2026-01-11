const tokenKey = "mindspace_token";

const api = async (path, options = {}) => {
  const headers = options.headers || {};
  const token = localStorage.getItem(tokenKey);
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(path, { ...options, headers });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }
  if (!response.ok) {
    const message = data && data.error ? data.error : "Request failed";
    throw new Error(message);
  }
  return data;
};

const redirectIfAuthed = async () => {
  if (!localStorage.getItem(tokenKey)) {
    return;
  }
  try {
    await api("/api/me");
    window.location.href = "/dashboard";
  } catch (error) {
    localStorage.removeItem(tokenKey);
  }
};

const setupAuthForm = () => {
  const form = document.querySelector("[data-auth-form]");
  if (!form) {
    return;
  }
  const mode = form.getAttribute("data-auth-form");
  const message = document.getElementById("auth-message");
  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (message) {
      message.textContent = "";
    }
    try {
      const payload = {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
      };
      const data = await api(`/api/auth/${mode}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      localStorage.setItem(tokenKey, data.token);
      window.location.href = "/dashboard";
    } catch (error) {
      if (message) {
        message.textContent = error.message;
      }
    }
  });
  redirectIfAuthed();
};

const setupDashboard = () => {
  const entriesContainer = document.getElementById("entries");
  if (!entriesContainer) {
    return;
  }
  const logoutBtn = document.getElementById("logout");
  const entryMessage = document.getElementById("entry-message");
  const summary = document.getElementById("summary");
  const tagFilter = document.getElementById("tag-filter");
  const entryIdField = document.getElementById("entry-id");
  const saveBtn = document.getElementById("save");
  const updateBtn = document.getElementById("update");
  const cancelBtn = document.getElementById("cancel-edit");
  const uploadInput = document.getElementById("image-upload");
  const uploadButton = document.getElementById("upload-image");

  const requireAuth = async () => {
    if (!localStorage.getItem(tokenKey)) {
      window.location.href = "/login";
      return false;
    }
    try {
      await api("/api/me");
      return true;
    } catch (error) {
      localStorage.removeItem(tokenKey);
      window.location.href = "/login";
      return false;
    }
  };

  const refreshSummary = async () => {
    const data = await api("/api/dashboard/summary");
    const moods = data.sentiment_counts || {};
    summary.textContent = `${data.total_entries} entries · ${data.total_tags} tags · moods: +${moods.positive || 0} / ~${moods.neutral || 0} / -${moods.negative || 0}`;
  };

  const refreshTags = async () => {
    const tags = await api("/api/tags");
    tagFilter.innerHTML = '<option value="">All tags</option>';
    tags.forEach(tag => {
      const option = document.createElement("option");
      option.value = tag.name;
      option.textContent = `${tag.name} (${tag.count})`;
      tagFilter.appendChild(option);
    });
  };

  const updateEditState = isEditing => {
    if (isEditing) {
      saveBtn.classList.add("hidden");
      updateBtn.disabled = false;
      cancelBtn.disabled = false;
    } else {
      saveBtn.classList.remove("hidden");
      updateBtn.disabled = true;
      cancelBtn.disabled = true;
    }
  };

  const insertAtCursor = (field, value) => {
    const start = field.selectionStart || 0;
    const end = field.selectionEnd || 0;
    const text = field.value;
    field.value = text.slice(0, start) + value + text.slice(end);
    const cursor = start + value.length;
    field.setSelectionRange(cursor, cursor);
    field.focus();
  };

  const renderEntries = async () => {
    const search = document.getElementById("search").value.trim();
    const tag = tagFilter.value;
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (tag) params.append("tag", tag);
    const entries = await api(`/api/entries?${params.toString()}`);
    entriesContainer.innerHTML = "";
    if (!entries.length) {
      entriesContainer.innerHTML = '<p class="small">No entries yet.</p>';
      return;
    }
    entries.forEach(entry => {
      const card = document.createElement("div");
      card.className = "entry";
      card.dataset.entryId = entry.id;
      const title = entry.title ? entry.title : "Untitled";
      const sentiment = entry.sentiment ? entry.sentiment : "unscored";
      const tags = entry.tags.map(tag => `<span class="tag">${tag}</span>`).join("");
      const fullText = entry.text || "";
      const preview =
        fullText.length > 1000 ? `${fullText.slice(0, 1000)}...` : fullText;
      const createdAt = entry.created_at ? new Date(entry.created_at).toLocaleString() : "N/A";
      const updatedAt = entry.updated_at ? new Date(entry.updated_at).toLocaleString() : "N/A";
      card.innerHTML = `
        <strong>${title}</strong>
        <p class="small">Mood: ${sentiment}</p>
        <p class="small">Created: ${createdAt} · Updated: ${updatedAt}</p>
        <p class="entry-text">${preview}</p>
        <div>${tags}</div>
        <div class="entry-actions">
          <button class="ghost" data-edit-id="${entry.id}">Edit</button>
          <button class="ghost" data-delete-id="${entry.id}">Delete</button>
        </div>
      `;
      card.addEventListener("click", () => {
        window.open(`/entries/${entry.id}`, "_blank", "noopener");
      });
      card.querySelectorAll("button").forEach(button => {
        button.addEventListener("click", event => event.stopPropagation());
      });
      entriesContainer.appendChild(card);
    });
    entriesContainer.querySelectorAll("[data-edit-id]").forEach(button => {
      button.addEventListener("click", () => {
        const entry = entries.find(item => item.id === Number(button.dataset.editId));
        if (!entry) return;
        entryIdField.value = entry.id;
        document.getElementById("title").value = entry.title || "";
        document.getElementById("text").value = entry.text || "";
        document.getElementById("tags").value = entry.tags.join(", ");
        entryMessage.textContent = "Editing entry. Update or cancel.";
        updateEditState(true);
      });
    });
    entriesContainer.querySelectorAll("[data-delete-id]").forEach(button => {
      button.addEventListener("click", async () => {
        const entryId = button.dataset.deleteId;
        if (!confirm("Delete this entry?")) return;
        try {
          await api(`/api/entries/${entryId}`, { method: "DELETE" });
          await refreshSummary();
          await refreshTags();
          await renderEntries();
        } catch (error) {
          entryMessage.textContent = error.message;
        }
      });
    });
  };

  const saveEntry = async () => {
    entryMessage.textContent = "";
    if (entryIdField.value) {
      entryMessage.textContent = "Already editing. Update or cancel.";
      return;
    }
    try {
      const tags = document
        .getElementById("tags")
        .value.split(",")
        .map(tag => tag.trim())
        .filter(Boolean);
      const payload = {
        title: document.getElementById("title").value,
        text: document.getElementById("text").value,
        tags,
      };
      await api("/api/entries", { method: "POST", body: JSON.stringify(payload) });
      document.getElementById("title").value = "";
      document.getElementById("text").value = "";
      document.getElementById("tags").value = "";
      entryIdField.value = "";
      updateEditState(false);
      entryMessage.textContent = "Entry saved.";
      await refreshSummary();
      await refreshTags();
      await renderEntries();
    } catch (error) {
      entryMessage.textContent = error.message;
    }
  };

  const updateEntry = async () => {
    entryMessage.textContent = "";
    const entryId = entryIdField.value;
    if (!entryId) {
      entryMessage.textContent = "Select an entry to edit.";
      return;
    }
    try {
      const tags = document
        .getElementById("tags")
        .value.split(",")
        .map(tag => tag.trim())
        .filter(Boolean);
      const payload = {
        title: document.getElementById("title").value,
        text: document.getElementById("text").value,
        tags,
      };
      await api(`/api/entries/${entryId}`, { method: "PUT", body: JSON.stringify(payload) });
      entryIdField.value = "";
      document.getElementById("title").value = "";
      document.getElementById("text").value = "";
      document.getElementById("tags").value = "";
      updateEditState(false);
      entryMessage.textContent = "Entry updated.";
      await refreshSummary();
      await refreshTags();
      await renderEntries();
    } catch (error) {
      entryMessage.textContent = error.message;
    }
  };

  const cancelEdit = () => {
    entryIdField.value = "";
    document.getElementById("title").value = "";
    document.getElementById("text").value = "";
    document.getElementById("tags").value = "";
    entryMessage.textContent = "";
    updateEditState(false);
  };

  const exportEntries = async () => {
    entryMessage.textContent = "";
    try {
      const token = localStorage.getItem(tokenKey);
      const response = await fetch("/api/entries/export?format=csv", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw new Error("Export failed");
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "entries.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      entryMessage.textContent = error.message;
    }
  };

  saveBtn.addEventListener("click", saveEntry);
  updateBtn.addEventListener("click", updateEntry);
  cancelBtn.addEventListener("click", cancelEdit);
  uploadButton?.addEventListener("click", async () => {
    entryMessage.textContent = "";
    if (!uploadInput || !uploadInput.files.length) {
      entryMessage.textContent = "Select an image to upload.";
      return;
    }
    const form = new FormData();
    form.append("image", uploadInput.files[0]);
    try {
      const token = localStorage.getItem(tokenKey);
      const response = await fetch("/api/uploads", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Upload failed");
      }
      const textarea = document.getElementById("text");
      const alt = uploadInput.files[0].name;
      insertAtCursor(textarea, `![${alt}](${data.url})`);
      uploadInput.value = "";
      entryMessage.textContent = "Image inserted.";
    } catch (error) {
      entryMessage.textContent = error.message;
    }
  });
  document.getElementById("refresh").addEventListener("click", async () => {
    await refreshSummary();
    await refreshTags();
    await renderEntries();
  });
  document.getElementById("search").addEventListener("input", () => {
    renderEntries();
  });
  tagFilter.addEventListener("change", () => {
    renderEntries();
  });
  document.getElementById("export").addEventListener("click", exportEntries);
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem(tokenKey);
    window.location.href = "/login";
  });

  requireAuth().then(async ok => {
    if (!ok) return;
    updateEditState(false);
    await refreshSummary();
    await refreshTags();
    await renderEntries();
  });
};

setupAuthForm();
setupDashboard();
const setupEntryDetail = () => {
  const detail = document.getElementById("entry-detail");
  if (!detail) {
    return;
  }
  const entryId = detail.dataset.entryId;
  if (!entryId) {
    return;
  }
  const titleEl = document.getElementById("entry-title");
  const metaEl = document.getElementById("entry-meta");
  const tagsEl = document.getElementById("entry-tags");
  const bodyEl = document.getElementById("entry-body");

  const loadEntry = async () => {
    if (!localStorage.getItem(tokenKey)) {
      window.location.href = "/login";
      return;
    }
    try {
      const entry = await api(`/api/entries/${entryId}`);
      titleEl.textContent = entry.title || "Untitled";
      const createdAt = entry.created_at ? new Date(entry.created_at).toLocaleString() : "N/A";
      const updatedAt = entry.updated_at ? new Date(entry.updated_at).toLocaleString() : "N/A";
      metaEl.textContent = `Mood: ${entry.sentiment || "unscored"} · Created: ${createdAt} · Updated: ${updatedAt}`;
      tagsEl.innerHTML = entry.tags.map(tag => `<span class="tag">${tag}</span>`).join("");
      bodyEl.innerHTML = entry.rendered_html || entry.text || "";
    } catch (error) {
      titleEl.textContent = "Entry not found.";
      metaEl.textContent = error.message;
    }
  };

  loadEntry();
};
setupEntryDetail();
