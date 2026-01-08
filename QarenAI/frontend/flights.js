const results = document.getElementById("results");
const priceRange = document.getElementById("priceRange");
const priceLabel = document.getElementById("priceLabel");
const directOnly = document.getElementById("directOnly");
const sortBy = document.getElementById("sortBy");
const searchBtn = document.getElementById("searchFlightsBtn");

let allFlights = [];
let filteredFlights = [];

// ===== تجهيز المطارات (للاستخدام القادم مع Amadeus) =====
function getAirportByCode(code) {
  return AIRPORTS.find(a => a.code === code);
}


/* بيانات تجريبية محسنة */
function mockFlights() {
  return [
    {
      airline: "الخطوط السعودية",
      price: 420,
      from: "RUH",
      to: "JED",
      depart: "08:10",
      arrive: "10:05",
      direct: true,
      stops: 0
    },
    {
      airline: "طيران ناس",
      price: 610,
      from: "RUH",
      to: "JED",
      depart: "07:00",
      arrive: "11:30",
      direct: false,
      stops: 1
    },
    {
      airline: "فلاي دبي",
      price: 390,
      from: "RUH",
      to: "DXB",
      depart: "09:20",
      arrive: "11:55",
      direct: true,
      stops: 0
    },
    {
      airline: "الخطوط الإماراتية",
      price: 820,
      from: "RUH",
      to: "DXB",
      depart: "14:00",
      arrive: "19:10",
      direct: false,
      stops: 1
    }
  ];
}

function renderFlights(list) {
  results.innerHTML = "";

  if (!list.length) {
    results.innerHTML = "<p>لا توجد نتائج</p>";
    return;
  }

  list.forEach(f => {
    const div = document.createElement("div");
    div.className = "flight-card";

    div.innerHTML = `
      <div class="flight-top">
        <div class="airline">${f.airline}</div>
        <div class="price">${f.price} SAR</div>
      </div>

      <div class="flight-middle">
        <div class="time">${f.depart}</div>
        <div class="route">${f.from} → ${f.to}</div>
        <div class="time">${f.arrive}</div>
      </div>

      <div class="flight-bottom">
        <div>${f.stops === 0 ? "مباشر" : `توقف ${f.stops}`}</div>
        <div class="badge">${f.direct ? "أفضل خيار" : "رحلة اقتصادية"}</div>
      </div>
    `;

    results.appendChild(div);
  });
}

function applyFilters() {
  const maxPrice = Number(priceRange.value);
  const direct = directOnly.checked;
  const sort = sortBy.value;

  filteredFlights = allFlights.filter(f =>
    f.price <= maxPrice && (!direct || f.direct)
  );

  if (sort === "cheap") filteredFlights.sort((a,b)=>a.price-b.price);
  if (sort === "expensive") filteredFlights.sort((a,b)=>b.price-a.price);
  if (sort === "direct") filteredFlights.sort((a,b)=>b.direct-a.direct);

  priceLabel.innerText = maxPrice + " SAR";
  renderFlights(filteredFlights);
}

searchBtn.onclick = () => {
  allFlights = mockFlights();
  const max = Math.max(...allFlights.map(f=>f.price));
  priceRange.max = max;
  priceRange.value = max;
  applyFilters();
};

priceRange.oninput = applyFilters;
directOnly.onchange = applyFilters;
sortBy.onchange = applyFilters;


