// prizes.js
const prizes = [
  {
    name: "Кольцо с бриллиантом",
    img: "/images/diamond_ring.png",
    starPrice: 5
  },
  {
    name: "Световой меч",
    img: "/images/light_sword.png",
    starPrice: 4
  },
  {
    name: "Браслет с гвоздями",
    img: "/images/nail_bracelet.png",
    starPrice: 3
  },
  {
    name: "Пасхальное яйцо",
    img: "/images/easter_egg.png",
    starPrice: 2
  },
  {
    name: "Шлем Неко",
    img: "/images/neko_helmet.png",
    starPrice: 2
  },
  {
    name: "Кольцо верности",
    img: "/images/bonded_ring.png",
    starPrice: 1
  },
  {
    name: "Любовное зелье",
    img: "/images/love_potion.png",
    starPrice: 1
  }
];

function showWinModal(prize) {
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-content';
  modalContent.innerHTML = `
    <div class="win-modal">
      <h2>Поздравляем!</h2>
      <div class="prize-display">
        <img src="${prize.img}" alt="${prize.name}" class="prize-img">
        <div class="prize-info">
          <h3>${prize.name}</h3>
          <p class="prize-value">${prize.starPrice}⭐</p>
        </div>
      </div>
      <p>Вы выиграли ${prize.name}!</p>
      <button class="modal-close-btn">Закрыть</button>
    </div>
  `;

  document.body.appendChild(modalContent);

  const closeBtn = modalContent.querySelector('.modal-close-btn');
  closeBtn.onclick = () => {
    modalContent.remove();
  };
}

function showWithdrawModal(gift) {
  const modalContent = document.createElement('div');
  modalContent.className = 'modal-content';
  modalContent.innerHTML = `
    <div class="withdraw-modal">
      <h2>Вывод подарка</h2>
      <div class="prize-display">
        <img src="${gift.img}" alt="${gift.name}" class="prize-img">
        <div class="prize-info">
          <h3>${gift.name}</h3>
          <p class="prize-value">${gift.starPrice}⭐</p>
        </div>
      </div>
      <p>Для вывода подарка, пожалуйста, напишите в чат боту команду:</p>
      <div class="command-box">
        <code>/withdraw ${gift.name}</code>
      </div>
      <button class="modal-close-btn">Закрыть</button>
    </div>
  `;

  document.body.appendChild(modalContent);

  const closeBtn = modalContent.querySelector('.modal-close-btn');
  closeBtn.onclick = () => {
    modalContent.remove();
  };
}

function getPrizeWidth() {
  const prize = document.querySelector('.prize');
  return prize ? prize.offsetWidth : 150;
}