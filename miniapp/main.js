const form = document.getElementById("recipe-form");
const statusBadge = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");

const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
}

function setStatus(text, isError = false) {
  statusBadge.textContent = text;
  statusBadge.style.background = isError ? "#fee2e2" : "#e2e8f0";
  statusBadge.style.color = isError ? "#b91c1c" : "#0f172a";
}

function collectExtras() {
  return Array.from(document.querySelectorAll("input[name='extras']:checked")).map(
    (checkbox) => checkbox.value
  );
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const ingredients = document.getElementById("ingredients").value.trim();
  const diet = document.getElementById("diet").value;
  const goal = document.getElementById("goal").value.trim();
  const extras = collectExtras();

  if (!ingredients) {
    setStatus("Нужно заполнить продукты", true);
    return;
  }

  const payload = {
    source: "miniapp",
    ingredients,
    diet,
    goal,
    extras,
    submitted_at: new Date().toISOString(),
  };

  setStatus("Отправляю…");
  submitBtn.disabled = true;

  const serialized = JSON.stringify(payload);

  if (tg) {
    tg.sendData(serialized);
    tg.close();
  } else {
    console.log("Mini app payload:", serialized);
    alert("Данные отправлены (эмуляция)");
  }

  setStatus("Готов");
  submitBtn.disabled = false;
  form.reset();
});

