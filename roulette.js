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

  // Динамически вычисляем ширину приза
  const tempPrize = document.createElement('div');
  tempPrize.className = 'prize';
  tempPrize.style.visibility = 'hidden';
  tempPrize.textContent = 'test';
  roulette.appendChild(tempPrize);
  const prizeWidth = tempPrize.offsetWidth +
    parseInt(getComputedStyle(tempPrize).marginLeft) +
    parseInt(getComputedStyle(tempPrize).marginRight);
  roulette.removeChild(tempPrize);

  const prizeCount = prizes.length;
  const extended = [...prizes, ...prizes, ...prizes];
  roulette.innerHTML = '';
  extended.forEach(prize => {
    const div = document.createElement('div');
    div.className = 'prize';
    div.textContent = `${prize.name} (${prize.price}₽)`;
    roulette.appendChild(div);
  });

  // Количество видимых призов
  const visibleCount = Math.floor(roulette.parentElement.offsetWidth / prizeWidth);
  const centerIndex = Math.floor(visibleCount / 2);

  const randomIndex = Math.floor(Math.random() * prizeCount);
  const stopIndex = prizeCount + randomIndex;
  const offset = (stopIndex - centerIndex) * prizeWidth;

  roulette.style.transition = 'transform 4s cubic-bezier(0.25, 0.1, 0.25, 1)';
  roulette.style.transform = `translateX(-${offset}px)`;

  setTimeout(() => {
    // Получаем текущее смещение transform
    const transform = roulette.style.transform;
    const match = /translateX\\(-?(\\d+)px\\)/.exec(transform);
    let currentOffset = offset;
    if (match) {
      currentOffset = parseInt(match[1]);
    }

    // Индекс центрального приза в extended
    const centerPrizeIndex = Math.round(currentOffset / prizeWidth) + centerIndex;
    // Индекс в оригинальном массиве
    const prizeIndexUnderPointer = centerPrizeIndex % prizeCount;
    const prizeUnderPointer = prizes[prizeIndexUnderPointer];

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
