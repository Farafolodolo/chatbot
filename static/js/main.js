class WelcomePage {
    constructor() {
        this.chatList = document.getElementById('chatList');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.errorMessage = document.getElementById('errorMessage');
        
        this.initializeEventListeners();
        this.loadChatHistory();
    }

    initializeEventListeners() {
        this.newChatBtn.addEventListener('click', () => this.createNewChat());
    }

    async loadChatHistory() {
        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('/get_chats');
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al cargar el historial');
            }

            this.renderChatHistory(data.results);
        } catch (error) {
            console.error('Error loading chat history:', error);
            this.renderEmptyState('Error al cargar las conversaciones. Intenta nuevamente.');
        } finally {
            this.showLoading(false);
        }
    }

    renderChatHistory(chats) {
        if (!chats || chats.length === 0) {
            this.renderEmptyState();
            return;
        }

        const chatListHTML = chats.map(chat => {
            // Mejorar la obtención del primer mensaje
            const firstMessage = this.getFirstUserMessage(chat.chat);
            const formattedDate = this.formatDate(chat.fecha_creada);
            
            return `
                <div class="chat-item" onclick="window.chatPage.openChat('${chat._id}')">
                    <div class="chat-preview">
                        ${firstMessage || 'Nueva conversación'}
                    </div>
                    <div class="chat-date">
                        <i class="fas fa-clock"></i>
                        ${formattedDate}
                    </div>
                </div>
            `;
        }).join('');

        this.chatList.innerHTML = `<div class="chat-list">${chatListHTML}</div>`;
    }

    getFirstUserMessage(chatHistory) {
        // Validar que chatHistory existe y es un array
        if (!chatHistory || !Array.isArray(chatHistory) || chatHistory.length === 0) {
            return null;
        }

        // Buscar el primer mensaje de usuario
        const firstUserMessage = chatHistory.find(msg => {
            // Verificar diferentes posibles estructuras de datos
            return msg && (
                msg.sender === 'user' || 
                msg.role === 'user' || 
                msg.usuario // para el caso específico de tu estructura
            );
        });

        // Retornar el contenido del mensaje basado en la estructura encontrada
        if (firstUserMessage) {
            return firstUserMessage.message || 
                    firstUserMessage.content || 
                    firstUserMessage.usuario || 
                    'Mensaje de usuario';
        }

        // Si no hay mensajes de usuario, buscar el primer mensaje disponible
        const firstMessage = chatHistory[0];
        if (firstMessage) {
            return firstMessage.message || 
                    firstMessage.content || 
                    firstMessage.usuario || 
                    firstMessage.chatbot || 
                    'Conversación iniciada';
        }

        return null;
    }

    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            const now = new Date();
            
            // Verificar que la fecha es válida
            if (isNaN(date.getTime())) {
                return 'Fecha inválida';
            }
            
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDays === 1) {
                return 'Hoy';
            } else if (diffDays === 2) {
                return 'Ayer';
            } else if (diffDays <= 7) {
                return `Hace ${diffDays - 1} días`;
            } else {
                return date.toLocaleDateString('es-ES', {
                    day: 'numeric',
                    month: 'short',
                    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
                });
            }
        } catch (error) {
            console.error('Error formatting date:', error);
            return 'Fecha inválida';
        }
    }

    renderEmptyState(message = null) {
        const emptyHTML = `
            <div class="empty-state">
                <i class="fas fa-comments"></i>
                <h3>${message || 'No hay conversaciones aún'}</h3>
                <p>${message || 'Inicia tu primera conversación con el botón de arriba'}</p>
            </div>
        `;
        this.chatList.innerHTML = emptyHTML;
    }

    async createNewChat() {
        this.setButtonLoading(true);
        this.hideError();

        try {
            const response = await fetch('/insert_new_chat');
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Error al crear el chat');
            }

            // Redirigir al nuevo chat
            window.location.href = `/chat?chat_id=${data.results}`;
        } catch (error) {
            console.error('Error creating new chat:', error);
            this.showError('Error al crear la conversación. Intenta nuevamente.');
        } finally {
            this.setButtonLoading(false);
        }
    }

    openChat(chatId) {
        window.location.href = `/chat?chat_id=${chatId}`;
    }

    showLoading(show) {
        this.loadingSpinner.style.display = show ? 'flex' : 'none';
    }

    setButtonLoading(loading) {
        if (loading) {
            this.newChatBtn.classList.add('btn-loading');
            this.newChatBtn.disabled = true;
        } else {
            this.newChatBtn.classList.remove('btn-loading');
            this.newChatBtn.disabled = false;
        }
    }

    showError(message) {
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        setTimeout(() => this.hideError(), 5000);
    }

    hideError() {
        this.errorMessage.style.display = 'none';
    }
}

// Initialize the welcome page
document.addEventListener('DOMContentLoaded', () => {
    window.chatPage = new WelcomePage();
});