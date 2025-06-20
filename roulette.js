const gifts = [
  { name: "Книга", stars: 80 },
  { name: "Котик", stars: 150 },
  { name: "Плюшевый медведь", stars: 100 },
  { name: "Сердце", stars: 50 },
  { name: "Робот", stars: 250 },
  { name: "Звезда", stars: 300 }
];

const rouletteDiv = document.getElementById("roulette");
const resultDiv = document.getElementById("result");
const spinBtn = document.getElementById("spin");

let tg = window.Telegram.WebApp;
tg.expand();

function renderGifts(highlightIndex = -1) {
  rouletteDiv.innerHTML = "";
  gifts.forEach((gift, index) => {
    const div = document.createElement("div");
    div.className = "gift" + (index === highlightIndex ? " highlight" : "");
    div.innerHTML = `<strong>${gift.name}</strong><br>${gift.stars}⭐`;
    rouletteDiv.appendChild(div);
  });
}

function spinRoulette() {
  let i = 0;
  let current = 0;
  const total = 20 + Math.floor(Math.random() * 10);
  const interval = setInterval(() => {
    renderGifts(current % gifts.length);
    current++;
    i++;
    if (i >= total) {
      clearInterval(interval);
      const selected = gifts[(current - 1) % gifts.length];
      resultDiv.innerHTML = `🎉 Вы выиграли: <b>${selected.name}</b> за ${selected.stars}⭐`;

      // Отправим результат боту
      tg.sendData(JSON.stringify(selected));
    }
  }, 100);
}

renderGifts();

spinBtn.addEventListener("click", spinRoulette);
