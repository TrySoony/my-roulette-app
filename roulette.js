let prizes = [];

async function fetchPrizes() {
  const response = await fetch('https://your-domain.com/prizes');
  prizes = await response.json();
  renderPrizes();
}

const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');

function renderPrizes() {
  roulette.innerHTML = '';
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
  const prizeWidth = 120; // ширина .prize + margin
  // Центрируем указатель на центральный приз
  const centerIndex = Math.floor(prizeCount / 2);
  const randomIndex = Math.floor(Math.random() * prizeCount);
  const stopIndex = prizeCount + randomIndex; // чтобы анимация была длиннее
  const offset = stopIndex * prizeWidth - (roulette.parentElement.offsetWidth / 2) + (prizeWidth / 2);

  roulette.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
  roulette.style.transform = `translateX(-${offset}px)`;

  setTimeout(() => {
    // Вычисляем, какой приз оказался под указателем
    const pointerPos = roulette.parentElement.offsetWidth / 2;
    const finalOffset = offset % (prizeCount * prizeWidth);
    const prizeUnderPointer = prizes[(randomIndex) % prizeCount];

    resultDiv.textContent = `Вы выиграли: ${prizeUnderPointer.name}!`;

    // Отправка результата в Telegram WebApp
    if (window.Telegram && Telegram.WebApp) {
      Telegram.WebApp.sendData(JSON.stringify({prize: prizeUnderPointer.name}));
      Telegram.WebApp.close();
    }

    spinBtn.disabled = false;
  }, 4000);
}

fetchPrizes();
spinBtn.addEventListener('click', spinRoulette);
