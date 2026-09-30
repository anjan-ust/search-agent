const form = document.getElementById("search-form");
const dropzone = document.getElementById("dropzone");
const imageInput = document.getElementById("image-input");
const preview = document.getElementById("preview");
const placeholder = document.getElementById("dropzone-placeholder");
const submitBtn = document.getElementById("submit-btn");
const progressPanel = document.getElementById("progress-panel");
const stepsList = document.getElementById("steps");
const resultsSection = document.getElementById("results-section");
const resultsGrid = document.getElementById("results-grid");
const resultsCount = document.getElementById("results-count");
const errorBanner = document.getElementById("error-banner");
const warningsBanner = document.getElementById("warnings-banner");
const pincodeBanner = document.getElementById("pincode-banner");

let stepEls = {};

async function loadSteps() {
  const res = await fetch("/api/steps");
  const steps = await res.json();
  stepsList.innerHTML = "";
  stepEls = {};
  for (const step of steps) {
    const li = document.createElement("li");
    li.innerHTML = `<span class="dot"></span><span>${step.label}</span>`;
    stepsList.appendChild(li);
    stepEls[step.node] = li;
  }
}

function markStepDone(node) {
  const el = stepEls[node];
  if (el) el.classList.add("done");
}

function resetPanels() {
  errorBanner.classList.add("hidden");
  warningsBanner.classList.add("hidden");
  pincodeBanner.classList.add("hidden");
  resultsSection.classList.add("hidden");
  resultsGrid.innerHTML = "";
  Object.values(stepEls).forEach((el) => el.classList.remove("done"));
}

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("drag-over");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("drag-over");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) {
    imageInput.files = e.dataTransfer.files;
    showPreview(file);
  }
});

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (file) showPreview(file);
});

function showPreview(file) {
  const url = URL.createObjectURL(file);
  preview.src = url;
  preview.classList.remove("hidden");
  placeholder.classList.add("hidden");
}

function pillClass(status) {
  if (["available", "deliverable"].includes(status)) return "ok";
  if (["unavailable", "not_deliverable"].includes(status)) return "bad";
  if (status === true) return "ok";
  if (status === false) return "warn";
  return "warn";
}

function renderCard(candidate) {
  const card = document.createElement("div");
  card.className = "card";

  const thumb = document.createElement("img");
  thumb.className = "card-thumb";
  thumb.src = candidate.thumbnail || "";
  thumb.alt = candidate.title || "";
  thumb.onerror = () => {
    thumb.style.display = "none";
  };

  const price = candidate.price
    ? `${candidate.currency || ""} ${candidate.price}`.trim()
    : "Price unknown";

  card.innerHTML = `
    <div class="card-body">
      <div class="card-title">${escapeHtml(candidate.title || "Untitled")}</div>
      <div class="card-meta">
        <span>${escapeHtml(candidate.merchant || candidate.source_domain || "")}</span>
        <span class="card-price">${escapeHtml(price)}</span>
      </div>
      <div class="pills">
        <span class="pill ${pillClass(candidate.india_verified)}">${candidate.india_verified ? "India verified" : "India unverified"}</span>
        <span class="pill ${pillClass(candidate.size_status)}">size: ${candidate.size_status}</span>
        <span class="pill ${pillClass(candidate.pincode_status)}">pincode: ${candidate.pincode_status}</span>
        <span class="pill">${candidate.match_type}</span>
        <span class="pill">${(candidate.origin || []).join(" + ")}</span>
      </div>
      <div class="card-footer">
        <span class="score">score ${Number(candidate.score).toFixed(2)}</span>
        <a class="view-link" href="${candidate.link}" target="_blank" rel="noopener noreferrer">View product</a>
      </div>
    </div>
  `;
  card.prepend(thumb);
  return card;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function handleSubmit(e) {
  e.preventDefault();
  if (!imageInput.files[0]) return;

  resetPanels();
  progressPanel.classList.remove("hidden");
  submitBtn.disabled = true;

  const formData = new FormData();
  formData.append("image", imageInput.files[0]);
  formData.append("size", document.getElementById("size-input").value);
  const pincode = document.getElementById("pincode-input").value;
  formData.append("pincode", pincode);

  try {
    const res = await fetch("/api/search", { method: "POST", body: formData });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const chunks = buffer.split("\n\n");
      buffer = chunks.pop();

      for (const chunk of chunks) {
        const line = chunk.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        const event = JSON.parse(line.slice(6));
        handleEvent(event, pincode);
      }
    }
  } catch (err) {
    showError(err.message || "Something went wrong.");
  } finally {
    submitBtn.disabled = false;
  }
}

function handleEvent(event, pincode) {
  if (event.type === "step") {
    markStepDone(event.node);
  } else if (event.type === "done") {
    progressPanel.classList.add("hidden");
    resultsSection.classList.remove("hidden");
    resultsCount.textContent = `${event.results.length} found`;

    if (pincode) {
      pincodeBanner.textContent = `Pincode ${pincode} is not checked automatically — verify delivery yourself for these results.`;
      pincodeBanner.classList.remove("hidden");
    }

    if (event.errors && event.errors.length) {
      warningsBanner.textContent = `Warnings: ${event.errors.join(" | ")}`;
      warningsBanner.classList.remove("hidden");
    }

    if (event.results.length === 0) {
      resultsGrid.innerHTML = '<p class="muted">No results survived the filters. Try a different photo or relax the target size.</p>';
    } else {
      event.results.forEach((candidate) => resultsGrid.appendChild(renderCard(candidate)));
    }
  } else if (event.type === "error") {
    progressPanel.classList.add("hidden");
    showError(event.message);
  }
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
}

form.addEventListener("submit", handleSubmit);
loadSteps();
