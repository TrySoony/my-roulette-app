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
    div.textContent = `${prize.name} (${prize.price}₽)`;
    roulette.appendChild(div);
  });
}

function spinRoulette() {
  spinBtn.disabled = true;
  resultDiv.textContent = '';
  const prizeCount = prizes.length;
  const prizeWidth = 120; // или вычисляйте динамически, как выше
  const visibleCount = 5; // у вас видно 5 призов
  const centerIndex = Math.floor(visibleCount / 2);
  const randomIndex = Math.floor(Math.random() * prizeCount);
  const stopIndex = prizeCount + randomIndex;
  const offset = (stopIndex - centerIndex) * prizeWidth;

  roulette.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
  roulette.style.transform = `translateX(-${offset}px)`;

  setTimeout(() => {
    const prizeUnderPointer = prizes[randomIndex % prizeCount];
    resultDiv.textContent = `Вы выиграли: ${prizeUnderPointer.name} (${prizeUnderPointer.price}₽)!`;

    // Отправка результата в Telegram WebApp
    if (window.Telegram && Telegram.WebApp) {
      Telegram.WebApp.sendData(JSON.stringify({prize: prizeUnderPointer}));
      Telegram.WebApp.close();
    }

    spinBtn.disabled = false;
  }, 4000);
}

renderPrizes();
spinBtn.addEventListener('click', spinRoulette);
