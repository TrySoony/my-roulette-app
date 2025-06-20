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

function getPrizeWidth() {
  const tempPrize = document.createElement('div');
  tempPrize.className = 'prize';
  tempPrize.style.visibility = 'hidden';
  tempPrize.textContent = 'test';
  roulette.appendChild(tempPrize);
  const prizeWidth = tempPrize.offsetWidth +
    parseInt(getComputedStyle(tempPrize).marginLeft) +
    parseInt(getComputedStyle(tempPrize).marginRight);
  roulette.removeChild(tempPrize);
  return prizeWidth;
}

function spinRoulette() {
  spinBtn.disabled = true;
  resultDiv.textContent = '';

  renderPrizes();

  const prizeCount = prizes.length;
  const prizeWidth = getPrizeWidth();
  const visibleCount = Math.floor(roulette.parentElement.offsetWidth / prizeWidth);
  const centerIndex = Math.floor(visibleCount / 2);

  const randomIndex = Math.floor(Math.random() * prizeCount);
  const stopIndex = prizeCount + randomIndex;
  const offset = (stopIndex - centerIndex) * prizeWidth;

  roulette.style.transition = 'transform 4s cubic-bezier(0.15, 0.85, 0.35, 1)';
  roulette.style.transform = `translateX(-${offset}px)`;

  setTimeout(() => {
    // Получаем координаты pointer
    const pointer = document.querySelector('.pointer');
    const pointerRect = pointer.getBoundingClientRect();
    // Получаем все призы
    const prizeDivs = document.querySelectorAll('.prize');
    let foundPrize = null;
    prizeDivs.forEach(div => {
      const rect = div.getBoundingClientRect();
      // Проверяем, находится ли центр pointer внутри div
      if (
        pointerRect.left >= rect.left &&
        pointerRect.left <= rect.right
      ) {
        foundPrize = div.textContent;
      }
    });

    // Находим приз по тексту
    let prizeUnderPointer = null;
    if (foundPrize) {
      prizeUnderPointer = prizes.find(prize => foundPrize.startsWith(prize.name));
    }

    // Фолбэк, если не найдено (на всякий случай)
    if (!prizeUnderPointer) {
      prizeUnderPointer = prizes[randomIndex % prizeCount];
    }

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
