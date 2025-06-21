document.addEventListener('DOMContentLoaded', () => {
    // Инициализируем Telegram WebApp
    if (window.Telegram && Telegram.WebApp) {
        Telegram.WebApp.ready();
        const user = Telegram.WebApp.initDataUnsafe.user;
        if (user && user.id) {
            fetchAdminData(user.id);
        } else {
            document.body.innerHTML = '<h1>Ошибка: Не удалось получить ID пользователя. Пожалуйста, откройте эту страницу через вашего Telegram-бота.</h1>';
        }
    } else {
        document.body.innerHTML = '<h1>Ошибка: Это приложение должно быть запущено внутри Telegram.</h1>';
        // Для отладки можно использовать фейковый ID
        // const fakeAdminId = 123456789; 
        // fetchAdminData(fakeAdminId);
    }
});

async function fetchAdminData(adminId) {
    try {
        // Запрашиваем оба типа данных, передавая ID админа
        const [connectionsRes, userDataRes] = await Promise.all([
            fetch(`/api/admin/connections?user_id=${adminId}`),
            fetch(`/api/admin/user_data?user_id=${adminId}`)
        ]);

        if (connectionsRes.status === 403 || userDataRes.status === 403) {
            document.body.innerHTML = '<h1>Доступ запрещен. Эту панель может просматривать только администратор.</h1>';
            return;
        }

        if (connectionsRes.ok) {
            const connections = await connectionsRes.json();
            renderConnections(connections);
        } else {
            console.error('Failed to load connections');
        }

        if (userDataRes.ok) {
            const userData = await userDataRes.json();
            renderUserData(userData);
        } else {
            console.error('Failed to load user data');
        }

    } catch (error) {
        console.error('Error fetching admin data:', error);
    }
}

function renderConnections(connections) {
    const tableBody = document.querySelector('#connections-table tbody');
    if (!connections || connections.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="3">Нет активных подключений.</td></tr>';
        return;
    }
    tableBody.innerHTML = connections.map(conn => `
        <tr>
            <td>${conn.user_id}</td>
            <td>${conn.username || 'N/A'}</td>
            <td>${conn.business_connection_id}</td>
        </tr>
    `).join('');
}

function renderUserData(userData) {
    const container = document.getElementById('user-data-container');
    if (Object.keys(userData).length === 0) {
        container.innerHTML = '<p>Нет данных о пользователях.</p>';
        return;
    }
    container.innerHTML = Object.entries(userData).map(([userId, data]) => `
        <div class="user-card">
            <h3>User ID: ${userId}</h3>
            <p>Попыток сделано: ${data.attempts}</p>
            <h4>Выигранные призы:</h4>
            ${data.gifts.length > 0 ? `
                <ul class="admin-prize-list">
                    ${data.gifts.map(gift => `
                        <li>
                            <img src="${gift.img}" alt="${gift.name}">
                            <span>${gift.name} (${gift.starPrice}⭐)</span>
                            <small>Выигран: ${gift.date}</small>
                        </li>
                    `).join('')}
                </ul>
            ` : '<p>Нет призов.</p>'}
        </div>
    `).join('');
} 