
const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const dayKeys = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const shiftTypes = ["AM", "PM", "Mid-Shift"];

let filters = {
  days: [],
  shifts: [],
  names: []
};

function classifyShift(shift) {
  if (!shift || shift === "OFF" || shift === "SET" || shift === "REQ") return null;
  if (shift.includes("1015AM")) return "AM";
  if (shift.includes("415PM")) return "PM";
  return "Mid-Shift";
}

function initializeFilters() {
  // Day filters
  const dayContainer = document.getElementById("dayFilter");
  days.forEach((day) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = day;
    btn.dataset.value = day;
    btn.dataset.type = "day";
    btn.onclick = () => toggleFilter("days", day, btn);
    dayContainer.appendChild(btn);
  });

  // Shift filters
  const shiftContainer = document.getElementById("shiftFilter");
  shiftTypes.forEach((shift) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = shift;
    btn.dataset.value = shift;
    btn.dataset.type = "shift";
    btn.onclick = () => toggleFilter("shifts", shift, btn);
    shiftContainer.appendChild(btn);
  });

  // Name filters
  const nameContainer = document.getElementById("nameFilter");
  scheduleData.forEach((person) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn";
    btn.textContent = person.name;
    btn.dataset.value = person.name;
    btn.dataset.type = "name";
    btn.onclick = () => toggleFilter("names", person.name, btn);
    nameContainer.appendChild(btn);
  });

  // Reset button
  document.getElementById("resetBtn").addEventListener("click", resetFilters);

  renderTable();
}

function toggleFilter(type, value, btn) {
  const index = filters[type].indexOf(value);

  if (index > -1) {
    filters[type].splice(index, 1);
    btn.classList.remove("active");
  } else {
    filters[type].push(value);
    btn.classList.add("active");
  }

  renderTable();
}

function resetFilters() {
  filters = { days: [], shifts: [], names: [] };
  document.querySelectorAll(".filter-btn").forEach((btn) => btn.classList.remove("active"));
  renderTable();
}

function renderTable() {
  // Determine which columns to show
  const visibleDays = filters.days.length > 0 ? filters.days : days;
  const visibleDayIndices = visibleDays.map((day) => days.indexOf(day));

  // Build header
  const thead = document.getElementById("tableHead");
  let headerHTML = "<tr><th>Team Member</th>";

  visibleDayIndices.forEach((index) => {
    headerHTML += `<th>${days[index]}</th>`;
  });

  headerHTML += "</tr>";
  thead.innerHTML = headerHTML;

  // Filter data
  const filteredData = scheduleData.filter((person) => {
    // Filter by name
    if (filters.names.length > 0 && !filters.names.includes(person.name)) return false;

    // Day/shift logic
    if (filters.days.length > 0 || filters.shifts.length > 0) {
      let matchesAllCriteria = true;

      if (filters.days.length > 0) {
        let matchesDay = false;

        filters.days.forEach((day) => {
          const dayIndex = days.indexOf(day);
          const dayKey = dayKeys[dayIndex];
          const shift = person[dayKey];

          if (filters.shifts.length > 0) {
            const shiftType = classifyShift(shift);
            if (shift && filters.shifts.includes(shiftType)) {
              matchesDay = true;
            }
          } else {
            if (shift && shift !== "OFF") {
              matchesDay = true;
            }
          }
        });

        matchesAllCriteria = matchesDay;
      } else if (filters.shifts.length > 0) {
        let hasShift = false;

        dayKeys.forEach((key) => {
          const shiftType = classifyShift(person[key]);
          if (filters.shifts.includes(shiftType)) {
            hasShift = true;
          }
        });

        matchesAllCriteria = hasShift;
      }

      if (!matchesAllCriteria) return false;
    }

    return true;
  });

  // Build body
  const tbody = document.getElementById("tableBody");
  tbody.innerHTML = "";

  if (filteredData.length === 0) {
    tbody.innerHTML = `<tr><td colspan="${visibleDayIndices.length + 1}" class="no-results">No matches found</td></tr>`;
    document.getElementById("resultsInfo").textContent = "No team members match your filters.";
    return;
  }

  filteredData.forEach((person) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td class="name-cell">${person.name}</td>`;

    visibleDayIndices.forEach((dayIndex) => {
      const dayKey = dayKeys[dayIndex];
      const shiftData = person[dayKey];

      const shifts = Array.isArray(shiftData) ? shiftData : (shiftData ? [shiftData] : []);

      let cellHTML = "";

      if (shifts.length > 0) {
        cellHTML = shifts.map((shift) => {
          const shiftType = classifyShift(shift);
          let badgeClass = "shift-off";

          if (shiftType === "AM") badgeClass = "shift-am";
          else if (shiftType === "PM") badgeClass = "shift-pm";
          else if (shiftType === "Mid-Shift") badgeClass = "shift-mid";
          else if (shift === "SET") badgeClass = "shift-set";
          else if (shift === "REQ") badgeClass = "shift-req";

          return `<span class="shift-badge ${badgeClass}">${shift}</span>`;
        }).join("<br>");
      } else {
        cellHTML = `<span class="shift-badge shift-off"></span>`;
      }

      const cell = document.createElement("td");
      cell.innerHTML = cellHTML;
      row.appendChild(cell);
    });

    tbody.appendChild(row);
  });

  // Update results info
  const filterSummary = [];
  if (filters.days.length > 0) filterSummary.push(`${filters.days.join(", ")}`);
  if (filters.shifts.length > 0) filterSummary.push(`${filters.shifts.join(", ")} shift${filters.shifts.length > 1 ? "s" : ""}`);
  if (filters.names.length > 0) filterSummary.push(`${filters.names.join(", ")}`);

  const summaryText =
    filterSummary.length > 0
      ? `Showing ${filteredData.length} result${filteredData.length !== 1 ? "s" : ""} for: ${filterSummary.join(" + ")}`
      : `Showing all ${filteredData.length} team members`;

  document.getElementById("resultsInfo").textContent = summaryText;
}

initializeFilters();

