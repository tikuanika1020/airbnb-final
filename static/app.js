const statusEl = document.getElementById("status");
const resultTitleEl = document.getElementById("resultTitle");
const tableContainerEl = document.getElementById("tableContainer");
const pipelineContainerEl = document.getElementById("pipelineContainer");
const loadDataBtn = document.getElementById("loadDataBtn");
const queryButtons = document.querySelectorAll(".query-btn");
const navButtons = document.querySelectorAll(".nav-btn");
const sections = document.querySelectorAll(".content-section");

const listingsGridEl = document.getElementById("listingsGrid");
const reviewsListEl = document.getElementById("reviewsList");
const collectionsGridEl = document.getElementById("collectionsGrid");
const listingDetailEl = document.getElementById("listingDetail");
const cityFilterEl = document.getElementById("cityFilter");
const refreshListingsBtn = document.getElementById("refreshListingsBtn");
const prevListingsBtn = document.getElementById("prevListingsBtn");
const nextListingsBtn = document.getElementById("nextListingsBtn");
const listingPageInfoEl = document.getElementById("listingPageInfo");

const state = {
  listingLimit: 24,
  listingSkip: 0,
  listingTotal: 0,
  city: "",
};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#b91c1c" : "#4b5563";
}

function sanitizeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function showSection(sectionId) {
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.section === sectionId);
  });
  sections.forEach((section) => {
    section.classList.toggle("hidden", section.id !== sectionId && section.id !== "listingDetailSection");
  });
}

function renderRows(rows) {
  if (!rows || rows.length === 0) {
    tableContainerEl.innerHTML = "<p>No results found.</p>";
    return;
  }

  const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  const headerHtml = columns.map((col) => `<th>${sanitizeHtml(col)}</th>`).join("");
  const bodyHtml = rows
    .map((row) => {
      const cells = columns
        .map((col) => `<td>${sanitizeHtml(row[col])}</td>`)
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  tableContainerEl.innerHTML = `
    <table>
      <thead><tr>${headerHtml}</tr></thead>
      <tbody>${bodyHtml}</tbody>
    </table>
  `;
}

function renderListings(rows) {
  if (!rows.length) {
    listingsGridEl.innerHTML = "<p>No listings found for this filter.</p>";
    return;
  }
  listingsGridEl.innerHTML = rows
    .map(
      (listing) => `
      <article class="listing-card" data-listing-id="${sanitizeHtml(listing.id)}">
        <div class="listing-photo"></div>
        <h3>${sanitizeHtml(listing.name || "Untitled Listing")}</h3>
        <p>${sanitizeHtml(listing.city || "")} - ${sanitizeHtml(listing.neighbourhood || "Unknown area")}</p>
        <p>${sanitizeHtml(listing.room_type || "Room")} - ${sanitizeHtml(listing.price || "N/A")}</p>
        <p>Rating: ${sanitizeHtml(listing.review_scores_rating || "N/A")} | Reviews: ${sanitizeHtml(listing.number_of_reviews || 0)}</p>
      </article>
    `
    )
    .join("");
}

function renderListingDetail(payload) {
  const listing = payload.listing;
  const reviewHtml = payload.reviews.length
    ? payload.reviews
        .map(
          (review) => `
          <li>
            <strong>${sanitizeHtml(review.reviewer_name || "Guest")}</strong> (${sanitizeHtml(review.date || "")})
            <p>${sanitizeHtml((review.comments || "").slice(0, 240))}</p>
          </li>
        `
        )
        .join("")
    : "<li>No reviews loaded for this listing yet.</li>";

  listingDetailEl.innerHTML = `
    <h3>${sanitizeHtml(listing.name || "Untitled Listing")}</h3>
    <p>${sanitizeHtml(listing.city || "")} - ${sanitizeHtml(listing.neighbourhood || "Unknown area")}</p>
    <p>${sanitizeHtml(listing.room_type || "Room")} | ${sanitizeHtml(listing.price || "N/A")} | accommodates ${sanitizeHtml(listing.accommodates || "N/A")}</p>
    <p>Host: ${sanitizeHtml(listing.host_name || "N/A")} | Minimum nights: ${sanitizeHtml(listing.minimum_nights || "N/A")} | Availability 365: ${sanitizeHtml(listing.availability_365 || "N/A")}</p>
    <h4>Recent Reviews</h4>
    <ul class="review-snippets">${reviewHtml}</ul>
  `;
}

function renderReviews(rows) {
  if (!rows.length) {
    reviewsListEl.innerHTML = "<p>No reviews loaded yet.</p>";
    return;
  }
  reviewsListEl.innerHTML = rows
    .map(
      (review) => `
      <article class="mini-card">
        <strong>${sanitizeHtml(review.reviewer_name || "Guest")}</strong>
        <p>${sanitizeHtml(review.city || "")} | Listing ${sanitizeHtml(review.listing_id || "")} | ${sanitizeHtml(review.date || "")}</p>
        <p>${sanitizeHtml((review.comments || "").slice(0, 220))}</p>
      </article>
    `
    )
    .join("");
}

function renderCollections(rows) {
  if (!rows.length) {
    collectionsGridEl.innerHTML = "<p>No collection data available.</p>";
    return;
  }
  collectionsGridEl.innerHTML = rows
    .map(
      (row) => `
      <article class="collection-card">
        <h3>${sanitizeHtml(row.neighbourhood || "Unknown")}</h3>
        <p>${sanitizeHtml(row.city || "")}</p>
        <p>Listings: ${sanitizeHtml(row.listingCount || 0)}</p>
        <p>Avg Price: $${sanitizeHtml(row.avgPrice || "N/A")}</p>
        <p>Avg Rating: ${sanitizeHtml(row.avgRating || "N/A")}</p>
      </article>
    `
    )
    .join("");
}

function updatePager() {
  const start = state.listingSkip + 1;
  const end = Math.min(state.listingSkip + state.listingLimit, state.listingTotal);
  listingPageInfoEl.textContent = state.listingTotal
    ? `Showing ${start}-${end} of ${state.listingTotal}`
    : "No listings loaded";
  prevListingsBtn.disabled = state.listingSkip === 0;
  nextListingsBtn.disabled = state.listingSkip + state.listingLimit >= state.listingTotal;
}

async function loadData() {
  setStatus("Loading larger dataset into MongoDB. This may take several minutes...");
  loadDataBtn.disabled = true;

  try {
    const response = await fetch("/api/load-data", { method: "POST" });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Failed to load data.");
    setStatus(
      `Loaded data. listings=${data.summary.listings}, reviews=${data.summary.reviews}, calendar=${data.summary.calendar}, neighborhoods=${data.summary.neighborhoods}`
    );
    await Promise.all([fetchListings(), fetchReviews(), fetchCollections()]);
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    loadDataBtn.disabled = false;
  }
}

async function fetchListings() {
  const params = new URLSearchParams({
    limit: String(state.listingLimit),
    skip: String(state.listingSkip),
  });
  if (state.city) params.append("city", state.city);

  const response = await fetch(`/api/listings?${params.toString()}`);
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "Failed loading listings.");
  state.listingTotal = data.total;
  renderListings(data.rows);
  updatePager();
}

async function fetchListingDetail(listingId) {
  const response = await fetch(`/api/listings/${listingId}`);
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "Failed loading listing detail.");
  renderListingDetail(data);
}

async function fetchReviews() {
  const response = await fetch("/api/reviews?limit=30");
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "Failed loading reviews.");
  renderReviews(data.rows);
}

async function fetchCollections() {
  const response = await fetch("/api/collections");
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "Failed loading collections.");
  renderCollections(data.rows);
}

async function runQuery(queryId) {
  setStatus(`Running Query ${queryId}...`);
  resultTitleEl.textContent = `Query ${queryId} Result`;
  tableContainerEl.innerHTML = "<p>Loading query results...</p>";

  try {
    const response = await fetch(`/api/query/${queryId}`);
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "Failed to run query.");
    setStatus(`Query ${queryId} complete (${data.count} rows).`);
    renderRows(data.rows);
    pipelineContainerEl.textContent = JSON.stringify(data.pipeline, null, 2);
    showSection("queriesSection");
  } catch (error) {
    setStatus(error.message, true);
    tableContainerEl.innerHTML = `<p>${sanitizeHtml(error.message)}</p>`;
  }
}

loadDataBtn.addEventListener("click", loadData);
refreshListingsBtn.addEventListener("click", async () => {
  state.listingSkip = 0;
  state.city = cityFilterEl.value;
  try {
    await fetchListings();
    setStatus("Listings refreshed.");
  } catch (error) {
    setStatus(error.message, true);
  }
});

prevListingsBtn.addEventListener("click", async () => {
  state.listingSkip = Math.max(0, state.listingSkip - state.listingLimit);
  try {
    await fetchListings();
  } catch (error) {
    setStatus(error.message, true);
  }
});

nextListingsBtn.addEventListener("click", async () => {
  state.listingSkip += state.listingLimit;
  try {
    await fetchListings();
  } catch (error) {
    setStatus(error.message, true);
  }
});

listingsGridEl.addEventListener("click", async (event) => {
  const card = event.target.closest(".listing-card");
  if (!card) return;
  try {
    await fetchListingDetail(card.dataset.listingId);
  } catch (error) {
    setStatus(error.message, true);
  }
});

queryButtons.forEach((button) => {
  button.addEventListener("click", () => runQuery(button.dataset.queryId));
});

navButtons.forEach((button) => {
  button.addEventListener("click", () => showSection(button.dataset.section));
});

async function boot() {
  try {
    await Promise.all([fetchListings(), fetchReviews(), fetchCollections()]);
    setStatus("Ready. Use Load Data to refresh from CSVs.");
  } catch (error) {
    setStatus(`Startup note: ${error.message}`, true);
  }
}

boot();
