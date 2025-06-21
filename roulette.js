const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');

let currentUser = {}; // Храним ID пользователя
let attemptsLeft = 0; // Храним оставшиеся попытки

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
  if (window.Telegram && Telegram.WebApp) {
    Telegram.WebApp.ready();
    currentUser = Telegram.WebApp.initDataUnsafe.user;
    if (currentUser && currentUser.id) {
      fetchUserStatus(currentUser.id);
    } else {
      // Пользователь не авторизован в Telegram, можно показать ошибку
      document.body.innerHTML = '<h1>Ошибка: не удалось получить данные пользователя. Откройте приложение через Telegram.</h1>';
    }
  } else {
    // Для отладки в браузере
    console.warn("Telegram WebApp is not available. Using mock user.");
    currentUser = { id: 'mock_user_123' };
    fetchUserStatus(currentUser.id);
  }
});

// Получаем статус пользователя с сервера
async function fetchUserStatus(userId) {
  try {
    const response = await fetch(`/api/get_user_status?user_id=${userId}`);
    const data = await response.json();
    if (response.ok) {
      attemptsLeft = data.attempts_left;
      updateSpinBtnState();
      updateGiftsList(data.gifts); // Сразу обновляем список подарков
    } else {
      console.error(data.error);
    }
  } catch (error) {
    console.error("Failed to fetch user status:", error);
  }
}

function updateSpinBtnState() {
  spinBtn.disabled = attemptsLeft <= 0;
  if (attemptsLeft <= 0) {
    spinBtn.textContent = 'Попытки закончились';
  } else {
    spinBtn.textContent = `Крутить! (${attemptsLeft} left)`;
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

// Функция для запуска конфетти-салюта
function launchConfetti() {
  const duration = 3 * 1000;
  const animationEnd = Date.now() + duration;
  const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 101 };

  function randomInRange(min, max) {
    return Math.random() * (max - min) + min;
  }

  const interval = setInterval(function() {
    const timeLeft = animationEnd - Date.now();
    if (timeLeft <= 0) {
      return clearInterval(interval);
    }
    const particleCount = 50 * (timeLeft / duration);
    // Запускаем конфетти с двух сторон для эффекта салюта
    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } });
    confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } });
  }, 250);
}

// Управление модальным окном
const winModalOverlay = document.getElementById('win-modal-overlay');
const winModalImg = document.getElementById('win-modal-img');
const winModalTitle = document.getElementById('win-modal-title');
const winModalPrice = document.getElementById('win-modal-price');
const winModalBtn = document.getElementById('win-modal-btn');

function showWinModal(prize) {
  winModalImg.src = prize.img;
  winModalTitle.textContent = prize.name;
  winModalPrice.textContent = `${prize.starPrice}⭐`;
  winModalOverlay.classList.add('visible');
  launchConfetti(); // Запускаем конфетти вместе с окном
}

function hideWinModal() {
  winModalOverlay.classList.remove('visible');
}

// Закрытие модального окна
winModalOverlay.addEventListener('click', (e) => {
  if (e.target === winModalOverlay) {
    hideWinModal();
  }
});
winModalBtn.addEventListener('click', () => {
  hideWinModal();
  // Переключаемся на вкладку "Мои подарки"
  document.querySelector('.tab-btn[data-tab="gifts"]').click();
});

async function spinRoulette() {
  if (attemptsLeft <= 0) return;
  spinBtn.disabled = true; // Сразу блокируем кнопку

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

  // Отправляем запрос на сервер для совершения спина
  try {
    const response = await fetch('/api/spin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUser.id })
    });
    
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Spin failed');
    }
    
    const prizeUnderPointer = data.won_prize;
    attemptsLeft--;
    updateSpinBtnState();
    
    // --- Запускаем анимацию на клиенте, зная результат ---
    const prizeIndex = prizes.findIndex(p => p.name === prizeUnderPointer.name);
    // ... (логика анимации остается примерно той же, но теперь `randomIndex` - это `prizeIndex`)
    // ...
    
    setTimeout(() => {
        if (prizeUnderPointer.starPrice > 0) {
            showWinModal(prizeUnderPointer);
            // Запрашиваем обновленные данные после выигрыша
            fetchUserStatus(currentUser.id); 
        } else {
            resultDiv.textContent = `Вы ничего не выиграли.`;
        }
    }, 5000);

  } catch (error) {
    console.error('Error during spin:', error);
    resultDiv.textContent = `Ошибка: ${error.message}`;
    spinBtn.disabled = false; // Разблокируем кнопку в случае ошибки
  }
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