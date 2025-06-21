const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');

// Максимум попыток
const MAX_ATTEMPTS = 2;

function getAttempts() {
  return parseInt(localStorage.getItem('roulette_attempts') || '0', 10);
}
function setAttempts(val) {
  localStorage.setItem('roulette_attempts', val);
}
function incAttempts() {
  setAttempts(getAttempts() + 1);
}
function isSpinAvailable() {
  return getAttempts() < MAX_ATTEMPTS;
}
function updateSpinBtnState() {
  spinBtn.disabled = !isSpinAvailable();
  if (!isSpinAvailable()) {
    spinBtn.textContent = 'Попытки закончились';
  } else {
    spinBtn.textContent = 'Крутить!';
  }
}

function renderPrizes(extendedPrizes) {
  roulette.innerHTML = '';
  extendedPrizes.forEach(prize => {
    const div = document.createElement('div');
    div.className = 'prize';
    if (prize.img) {
      div.innerHTML = `<img src="${prize.img}" class="prize-img" alt="${prize.name}">
                       <div class="prize-name">${prize.name}</div>
                       <div class="prize-price">${prize.starPrice}⭐</div>`;
    } else {
      div.innerHTML = `<div class="prize-name" style="font-size:18px;">${prize.name}</div>
                       <div class="prize-price" style="color:#bbb;">Пусто</div>`;
    }
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
  if (!isSpinAvailable()) return;
  incAttempts();
  updateSpinBtnState();

  // Сбрасываем старые анимации перед новым запуском
  document.querySelectorAll('.prize.prize-won').forEach(el => el.classList.remove('prize-won'));
  resultDiv.classList.remove('won');
  roulette.classList.remove('spinning');
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

  // Даем браузеру применить сброс классов перед добавлением нового
  requestAnimationFrame(() => {
    // Устанавливаем конечную точку как CSS-переменную
    roulette.style.setProperty('--spin-offset', `-${offset}px`);
    // Добавляем класс для запуска анимации в CSS
    roulette.classList.add('spinning');
  });

  setTimeout(() => {
    // Получаем координаты pointer
    const pointer = document.querySelector('.pointer');
    const pointerRect = pointer.getBoundingClientRect();
    // Получаем все призы
    const prizeDivs = document.querySelectorAll('.prize');
    let winningDiv = null;
    let foundPrizeText = null;

    prizeDivs.forEach(div => {
      const rect = div.getBoundingClientRect();
      if (
        pointerRect.left >= rect.left &&
        pointerRect.right >= pointerRect.right
      ) {
        winningDiv = div;
        foundPrizeText = div.querySelector('.prize-name').textContent;
      }
    });

    // Находим приз по названию
    let prizeUnderPointer = null;
    if (foundPrizeText) {
      prizeUnderPointer = prizes.find(prize => foundPrizeText === prize.name);
    }

    // Фолбэк, если не найдено (на всякий случай)
    if (!prizeUnderPointer) {
      prizeUnderPointer = prizes[randomIndex % prizeCount];
    }
    
    // Добавляем класс для анимации текста результата
    resultDiv.classList.add('won');

    if (prizeUnderPointer.starPrice > 0) {
      resultDiv.textContent = `Вы выиграли: ${prizeUnderPointer.name} (${prizeUnderPointer.starPrice}⭐)!`;
      saveGift(prizeUnderPointer);
      // Добавляем класс для анимации выигранного приза
      if (winningDiv) {
        winningDiv.classList.add('prize-won');
      }
    } else {
      resultDiv.textContent = `Вы ничего не выиграли.`;
    }

    // Отправка результата в Telegram WebApp
    if (window.Telegram && Telegram.WebApp) {
      Telegram.WebApp.sendData(JSON.stringify({prize: prizeUnderPointer}));
      // Не закрываем сразу, чтобы пользователь увидел результат
      // Telegram.WebApp.close(); 
    }

  }, 5000); // Таймер должен совпадать с длительностью анимации
}

// Сохраняем выигранный приз
function saveGift(prize) {
  if (prize.starPrice === 0) return; // не сохраняем пусто
  const gifts = JSON.parse(localStorage.getItem('my_gifts') || '[]');
  gifts.push({
    name: prize.name,
    img: prize.img,
    starPrice: prize.starPrice,
    date: new Date().toLocaleDateString('ru-RU')
  });
  localStorage.setItem('my_gifts', JSON.stringify(gifts));
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

// При загрузке страницы обновляем состояние кнопки
updateSpinBtnState();

spinBtn.addEventListener('click', spinRoulette);