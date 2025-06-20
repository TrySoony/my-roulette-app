const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');

function renderPrizes(extendedPrizes) {
  roulette.innerHTML = '';
  extendedPrizes.forEach(prize => {
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

  const prizeCount = prizes.length;
  const prizeWidth = getPrizeWidth();
  const visibleCount = Math.floor(roulette.parentElement.offsetWidth / prizeWidth);
  const centerIndex = Math.floor(visibleCount / 2);

  const randomIndex = Math.floor(Math.random() * prizeCount);
  const rounds = Math.floor(Math.random() * 3) + 5;
  const totalSteps = rounds * prizeCount + randomIndex;
  const extendedLength = totalSteps + visibleCount + 2;
  let extendedPrizes = [];
  while (extendedPrizes.length < extendedLength) {
    extendedPrizes = extendedPrizes.concat(prizes);
  }
  extendedPrizes = extendedPrizes.slice(0, extendedLength);

  renderPrizes(extendedPrizes);

  const offset = (totalSteps - centerIndex) * prizeWidth;

  // Сброс transform и transition (моментально)
  roulette.style.transition = 'none';
  roulette.style.transform = 'translateX(0px)';

  // Даем браузеру применить сброс (через requestAnimationFrame)
  requestAnimationFrame(() => {
    // Теперь задаём анимацию вправо
    roulette.style.transition = 'transform 2s cubic-bezier(0.15, 0.85, 0.35, 1)';
    roulette.style.transform = `translateX(-${offset}px)`;
  });

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
  }, 2000);
}

// Первичная отрисовка (по умолчанию 3 круга)
(function(){
  const prizeCount = prizes.length;
  const prizeWidth = getPrizeWidth();
  const visibleCount = Math.floor(roulette.parentElement.offsetWidth / prizeWidth);
  const rounds = 3;
  const totalSteps = rounds * prizeCount;
  const extendedLength = totalSteps + visibleCount + 2;
  let extendedPrizes = [];
  while (extendedPrizes.length < extendedLength) {
    extendedPrizes = extendedPrizes.concat(prizes);
  }
  extendedPrizes = extendedPrizes.slice(0, extendedLength);
  renderPrizes(extendedPrizes);
})();

spinBtn.addEventListener('click', spinRoulette);
