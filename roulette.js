const roulette = document.getElementById('roulette');
const spinBtn = document.getElementById('spin');
const resultDiv = document.getElementById('result');
const giftsList = document.getElementById('gifts-list');
const attemptsLeftSpan = document.getElementById('attempts-left');
const errorDiv = document.getElementById('error-message');

let currentUser = { id: null }; // Храним ID пользователя
let attemptsLeft = 0; // Храним оставшиеся попытки
let userGifts = [];
let telegramUser = null;
let spinInProgress = false;

function showError(message, duration = 5000) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
        errorDiv.textContent = '';
    }, duration);
}

function showSuccess(message) {
    alert(message);
}

function updateGiftsList(gifts) {
    if (!giftsList) return;
    
    if (!gifts || gifts.length === 0) {
        giftsList.innerHTML = '<p class="empty-state">У вас пока нет выигранных призов.</p>';
        return;
    }
    
    giftsList.innerHTML = `
        <h3>Ваши призы:</h3>
        <div class="gifts-grid">
            ${gifts.map(gift => `
                <div class="gift-item">
                    <img src="${gift.img}" alt="${gift.name}">
                    <p>${gift.name}</p>
                    <p>${gift.starPrice}⭐</p>
                    <p class="gift-date">${gift.date || 'Дата не указана'}</p>
                </div>
            `).join('')}
        </div>
    `;
}

function showWithdrawModal(gift) {
  const modal = document.getElementById('withdraw-info-modal-overlay');
  const img = document.getElementById('withdraw-info-img');
  const title = document.getElementById('withdraw-info-title');
  
  img.src = gift.img;
  title.textContent = gift.name;
  modal.classList.add('visible');
  
  // Обработчик для кнопки "Понятно"
  const closeBtn = document.getElementById('withdraw-info-btn');
  closeBtn.onclick = () => modal.classList.remove('visible');
  
  // Закрытие по клику на оверлей
  modal.onclick = (e) => {
    if (e.target === modal) {
      modal.classList.remove('visible');
    }
  };
}

function updateSpinBtnState() {
    const canSpin = attemptsLeft > 0 && !spinInProgress;
    spinBtn.disabled = !canSpin;
    spinBtn.textContent = canSpin ? 'Крутить!' : 'Нет попыток';
    if (attemptsLeftSpan) {
        attemptsLeftSpan.textContent = attemptsLeft;
    }
}

function renderPrizes(extendedPrizes) {
    roulette.innerHTML = '';
    extendedPrizes.forEach(prize => {
        const div = document.createElement('div');
        div.className = 'prize';
        if (prize.img) {
            div.innerHTML = `
                <img src="${prize.img}" class="prize-img" alt="${prize.name}">
                <div class="prize-name">${prize.name}</div>
                <div class="prize-price">${prize.starPrice}⭐</div>
            `;
        } else {
            div.innerHTML = `
                <div class="prize-name" style="font-size:18px;">${prize.name}</div>
                <div class="prize-price" style="color:#bbb;">Пусто</div>
            `;
        }
        roulette.appendChild(div);
    });
}

function getPrizeWidth() {
    const prizeElement = document.querySelector('.prize');
    return prizeElement ? prizeElement.offsetWidth : 100;
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
    if (spinInProgress) {
        showError("Подождите, рулетка еще крутится");
        return;
    }
    
    if (attemptsLeft <= 0) {
        showError("У вас не осталось попыток");
        return;
    }
    
    try {
        spinInProgress = true;
        spinBtn.disabled = true;
        updateSpinBtnState();
        
        // 1. Получаем результат с сервера
        const data = await fetch('/api/spin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (!data.ok) {
            const errorData = await data.json();
            throw new Error(errorData.error || 'Не удалось выполнить прокрутку');
        }

        const result = await data.json();
        const wonPrize = result.won_prize;
        
        // 2. Запускаем анимацию
        const prizeCount = prizes.length;
        const prizeWidth = getPrizeWidth();
        const visibleCount = Math.floor(roulette.parentElement.offsetWidth / prizeWidth);
        const centerIndex = Math.floor(visibleCount / 2);

        // Находим индекс выигранного приза
        const prizeIndex = prizes.findIndex(p => 
            p.name === wonPrize.name && 
            p.starPrice === wonPrize.starPrice
        );

        if (prizeIndex === -1) {
            throw new Error("Сервер вернул неизвестный приз");
        }

        const rounds = 5;
        const totalSteps = rounds * prizeCount + prizeIndex;
        const extendedLength = totalSteps + visibleCount + 2;
        let extendedPrizes = [];
        
        while (extendedPrizes.length < extendedLength) {
            extendedPrizes = extendedPrizes.concat(prizes);
        }
        extendedPrizes = extendedPrizes.slice(0, extendedLength);

        renderPrizes(extendedPrizes);
        
        // Сбрасываем старые анимации
        roulette.style.transition = 'none';
        roulette.style.transform = 'translateX(0)';
        roulette.classList.remove('spinning');

        // Даем браузеру обновиться
        await new Promise(resolve => requestAnimationFrame(resolve));

        const offset = (totalSteps - centerIndex) * prizeWidth;
        
        // Устанавливаем анимацию
        roulette.style.transition = 'transform 5s cubic-bezier(0.2, 0.8, 0.2, 1)';
        roulette.style.transform = `translateX(-${offset}px)`;

        // Обновляем состояние и показываем результат после завершения анимации
        roulette.addEventListener('transitionend', async () => {
            try {
                attemptsLeft = result.attempts_left;
                updateSpinBtnState();

                if (wonPrize.starPrice > 0) {
                    showWinModal(wonPrize);
                    // Обновляем список подарков
                    await fetchUserStatus(currentUser.id);
                } else {
                    resultDiv.textContent = 'К сожалению, вы ничего не выиграли в этот раз.';
                }
            } catch (error) {
                showError(`Ошибка при обновлении статуса: ${error.message}`);
            } finally {
                spinInProgress = false;
                updateSpinBtnState();
            }
        }, { once: true });

    } catch (error) {
        console.error('Error during spin:', error);
        showError(`Ошибка: ${error.message}`);
        spinInProgress = false;
        updateSpinBtnState();
    }
}

// Первичная отрисовка призов
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

function initializeApp() {
    try {
        const tg = window.Telegram.WebApp;
        if (!tg) {
            throw new Error("Telegram Web App не найден");
        }
        
        tg.ready();
        tg.expand();

        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            telegramUser = tg.initDataUnsafe.user;
            currentUser.id = telegramUser.id;
            
            announceUser(telegramUser.id)
                .then(() => fetchUserStatus(telegramUser.id))
                .catch(error => {
                    showError(`Ошибка инициализации: ${error.message}`);
                    spinBtn.disabled = true;
                });
        } else {
            let errorDetails = [
                `tg.initData: ${tg.initData}`,
                `tg.initDataUnsafe: ${JSON.stringify(tg.initDataUnsafe, null, 2)}`
            ];
            const friendlyMessage = "Это приложение должно запускаться из Telegram.\nПожалуйста, не открывайте ссылку напрямую в браузере. Вернитесь в бот и нажмите кнопку 'Открыть рулетку'.";
            showError("Ошибка: не удалось получить данные пользователя.\n\n" + friendlyMessage + "\n\n--- Техническая информация ---\n" + errorDetails.join('\n'));
            spinBtn.disabled = true;
        }
    } catch (e) {
        showError(`Критическая ошибка инициализации: ${e.message}. Приложение должно запускаться из Telegram.`);
        spinBtn.disabled = true;
    }
}

// Новая функция для создания/анонсирования пользователя на сервере
async function announceUser(userId) {
    if (!userId || typeof userId !== 'number' || userId <= 0) {
        throw new Error('Некорректный ID пользователя');
    }
    
    try {
        const response = await fetch('/api/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }
        
        const data = await response.json();
        console.log('User announced successfully:', data.message);
        currentUser.id = userId; // Устанавливаем ID текущего пользователя
        return data;
    } catch (error) {
        console.error("Error announcing user:", error);
        throw error;
    }
}

// Получаем статус пользователя с сервера
async function fetchUserStatus(userId) {
    if (!userId || typeof userId !== 'number' || userId <= 0) {
        throw new Error('Некорректный ID пользователя');
    }
    
    try {
        const response = await fetch(`/api/get_user_status?user_id=${userId}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Server error');
        }
        const data = await response.json();
        attemptsLeft = data.attempts_left;
        updateSpinBtnState();
        if (data.gifts) {
            userGifts = data.gifts;
            updateGiftsList(data.gifts);
        }
    } catch (error) {
        console.error("Failed to fetch user status:", error);
        throw error;
    }
}

// Обработчик нажатия на кнопку
spinBtn.addEventListener('click', spinRoulette);

// Инициализация приложения
initializeApp();