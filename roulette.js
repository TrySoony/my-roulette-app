const prizes = [
  "iPhone 15",
  "AirPods",
  "1000₽",
  "Пусто",
  "MacBook",
  "Чашка",
  "Пусто",
  "PlayStation 5",
  "Пусто",
  "Книга"
];

const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');

function renderPrizes() {
  roulette.innerHTML = '';
  // Дублируем призы для плавной анимации
  const extended = [...prizes, ...prizes, ...prizes];
  extended.forEach(prize => {
    const div = document.createElement('div');
    div.className = 'prize';
    div.textContent = prize;
    roulette.appendChild(div);
  });
}

function spinRoulette() {
  spinBtn.disabled = true;
  resultDiv.textContent = '';
  const prizeCount = prizes.length;
  const prizeWidth = 120; // ширина .prize + margin
  const randomIndex = Math.floor(Math.random() * prizeCount);
  const offset = (prizeCount + randomIndex) * prizeWidth - (roulette.parentElement.offsetWidth / 2) + (prizeWidth / 2);

  roulette.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
  roulette.style.transform = `translateX(-${offset}px)`;

  setTimeout(() => {
    const wonPrize = prizes[randomIndex];
    resultDiv.textContent = `Вы выиграли: ${wonPrize}!`;

    // Отправка результата в Telegram WebApp
    if (window.Telegram && Telegram.WebApp) {
      Telegram.WebApp.sendData(JSON.stringify({prize: wonPrize}));
      Telegram.WebApp.close(); // Закрыть WebApp (по желанию)
    }

    spinBtn.disabled = false;
  }, 4000);
}

renderPrizes();
spinBtn.addEventListener('click', spinRoulette);
