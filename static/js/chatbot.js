class ChatBot {
          constructor() {
              this.chatMessages = document.getElementById('chatMessages');
              this.messageInput = document.getElementById('messageInput');
              this.sendButton = document.getElementById('sendButton');
              this.topicSelect = document.getElementById('topicSelect');
              this.typingIndicator = document.getElementById('typingIndicator');
              this.errorMessage = document.getElementById('errorMessage');
              this.suggestionsDropdown = document.getElementById('suggestionsDropdown');
              
              this.currentChatId = null;
              this.isTyping = false;
              
              this.init();
          }

          init() {
              // Cargar chat existente si hay un chat_id en la URL o localStorage
              this.loadExistingChat();
              
              // Event listeners
              this.sendButton.addEventListener('click', () => this.handleSendMessage());
              this.messageInput.addEventListener('keypress', (e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      this.handleSendMessage();
                  }
              });
              
              // Auto-resize textarea
              this.messageInput.addEventListener('input', () => {
                  this.messageInput.style.height = 'auto';
                  this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
              });
          }

          // Función para cargar chat existente
          async loadExistingChat() {
              // Obtener chat_id desde el campo oculto en el HTML
              const chatIdField = document.getElementById('chat_id');
              if (chatIdField && chatIdField.value) {
                  this.currentChatId = chatIdField.value;
                  await this.loadChatMessages(this.currentChatId);
              }
          }

          // Función para cargar mensajes desde la base de datos
          async loadChatMessages(chatId) {
              try {
                  const response = await fetch('/get_chat', {
                      method: 'POST',
                      headers: {
                          'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({ chat_id: chatId })
                  });

                  const data = await response.json();
                  
                  if (data.status === 'successful' && data.results) {
                      this.renderChatHistory(data.results.chat);
                  } else {
                      console.error('Error loading chat:', data.message);
                      // Si no se puede cargar el chat, mostrar mensaje de bienvenida
                      this.showWelcomeMessage();
                  }
              } catch (error) {
                  console.error('Error fetching chat:', error);
                  this.showWelcomeMessage();
              }
          }

          // Función para renderizar el historial del chat
          renderChatHistory(chatHistory) {
              // Limpiar mensajes existentes (incluyendo mensaje de bienvenida)
              this.chatMessages.innerHTML = '';
              
              if (!chatHistory || chatHistory.length === 0) {
                  this.showWelcomeMessage();
                  return;
              }

              // Renderizar cada mensaje sin animación
              chatHistory.forEach(messageData => {
                  // Agregar mensaje del usuario
                  if (messageData.usuario) {
                      this.addMessageToChat(messageData.usuario, 'user', false);
                  }
                  
                  // Agregar respuesta del bot
                  if (messageData.bot) {
                      this.addMessageToChat(messageData.bot, 'bot', false, messageData.error);
                  }
              });

              // Scroll al final
              this.scrollToBottom();
          }

          // Función para mostrar mensaje de bienvenida
          showWelcomeMessage() {
              this.chatMessages.innerHTML = `
                  <div class="welcome-message">
                      <i class="fas fa-comments"></i>
                      <h3>¡Bienvenido!</h3>
                      <p>Selecciona un tema y hazme cualquier pregunta. Estoy aquí para ayudarte.</p>
                  </div>
              `;
          }

          // Función para agregar mensaje al chat
          addMessageToChat(message, sender, withAnimation = true, isError = false) {
              const messageDiv = document.createElement('div');
              messageDiv.className = `message message-${sender}`;
              
              // Solo agregar animación si se especifica
              if (withAnimation) {
                  messageDiv.style.animation = 'fadeInUp 0.5s ease';
              }

              const avatarIcon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
              const avatarClass = sender === 'user' ? 'message-avatar' : 'message-avatar';
              
              let messageContent = `
                  <div class="${avatarClass}">
                      <i class="${avatarIcon}"></i>
                  </div>
                  <div class="message-content">
                      ${message}
                  </div>
              `;

              messageDiv.innerHTML = messageContent;
              
              // Si es un mensaje de error del bot, agregar clase especial
              if (sender === 'bot' && isError) {
                  const messageContentEl = messageDiv.querySelector('.message-content');
                  messageContentEl.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)';
                  messageContentEl.style.color = 'white';
                  messageContentEl.style.border = '1px solid #ff6b6b';
              }

              this.chatMessages.appendChild(messageDiv);
              
              if (withAnimation) {
                  this.scrollToBottom();
              }
          }

          // Función para manejar el envío de mensajes
          async handleSendMessage() {
              const message = this.messageInput.value.trim();
              const topic = this.topicSelect.value;

              if (!message) {
                  this.showError('Por favor, escribe un mensaje');
                  return;
              }

              if (!topic) {
                  this.showError('Por favor, selecciona un tema');
                  return;
              }

              if (this.isTyping) {
                  return;
              }

              // Limpiar mensaje de bienvenida si existe
              const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
              if (welcomeMessage) {
                  welcomeMessage.remove();
              }

              // Agregar mensaje del usuario
              this.addMessageToChat(message, 'user', true);
              
              // Limpiar input
              this.messageInput.value = '';
              this.messageInput.style.height = 'auto';
              
              // Mostrar indicador de escritura
              this.showTypingIndicator();
              
              // Deshabilitar botón de envío
              this.sendButton.disabled = true;
              this.isTyping = true;

              try {
                  // Enviar mensaje al servidor usando tu ruta /ask
                  const response = await fetch('/ask', {
                      method: 'POST',
                      headers: {
                          'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                          pregunta: message,
                          tema: topic,
                          chat_id: this.currentChatId
                      })
                  });

                  const data = await response.json();
                  
                  // Ocultar indicador de escritura
                  this.hideTypingIndicator();
                  
                  if (response.ok && data.respuesta) {
                      // Agregar respuesta del bot con efecto de escritura
                      // Si el response es 404, significa que es un error
                      const isError = response.status === 404;
                      this.typewriterEffect(data.respuesta, isError);
                  } else {
                      this.addMessageToChat('Lo siento, ocurrió un error. Inténtalo de nuevo.', 'bot', true, true);
                  }
              } catch (error) {
                  console.error('Error:', error);
                  this.hideTypingIndicator();
                  this.addMessageToChat('Error de conexión. Por favor, inténtalo de nuevo.', 'bot', true, true);
              } finally {
                  this.sendButton.disabled = false;
                  this.isTyping = false;
              }
          }

          // Función para mostrar indicador de escritura
          showTypingIndicator() {
              this.typingIndicator.style.display = 'flex';
              this.scrollToBottom();
          }

          // Función para ocultar indicador de escritura
          hideTypingIndicator() {
              this.typingIndicator.style.display = 'none';
          }

          typewriterEffect(text, isError = false) {
              const messageDiv = document.createElement('div');
              messageDiv.className = 'message message-bot';
              
              messageDiv.innerHTML = `
                  <div class="message-avatar">
                      <i class="fas fa-robot"></i>
                  </div>
                  <div class="message-content">
                      <span class="typewriter-text"></span>
                  </div>
              `;

              const messageContent = messageDiv.querySelector('.message-content');
              const typewriterText = messageDiv.querySelector('.typewriter-text');
              
              if (isError) {
                  messageContent.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)';
                  messageContent.style.color = 'white';
                  messageContent.style.border = '1px solid #ff6b6b';
              }

              this.chatMessages.appendChild(messageDiv);
              this.scrollToBottom();

              let i = 0;
              const typeSpeed = 30;
              
              const typeTimer = setInterval(() => {
                  if (i < text.length) {
                      typewriterText.textContent += text.charAt(i);
                      i++;
                      this.scrollToBottom();
                  } else {
                      clearInterval(typeTimer);
                      typewriterText.classList.add('typing-complete');
                  }
              }, typeSpeed);
          }

          showError(message) {
              this.errorMessage.textContent = message;
              this.errorMessage.style.display = 'block';
              setTimeout(() => {
                  this.errorMessage.style.display = 'none';
              }, 3000);
          }

          // Función para hacer scroll al final
          scrollToBottom() {
              this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
          }
      }
      

      // Inicializar el chatbot cuando se carga la página
      document.addEventListener('DOMContentLoaded', () => {
          new ChatBot();
      });
// --- AUTOCOMPLETADO DE PREGUNTAS ---
let cachedQuestions = [];
let selectedSuggestionIndex = -1;

const topicSelect = document.getElementById('topicSelect');
const messageInput = document.getElementById('messageInput');
const suggestionsDropdown = document.getElementById('suggestionsDropdown');

// Fetch preguntas al cambiar de tema
topicSelect.addEventListener('change', async function() {
  const topic = this.value;
  cachedQuestions = [];
  suggestionsDropdown.style.display = 'none';
  selectedSuggestionIndex = -1;
  if (!topic) return;
  try {
      const res = await fetch('/get_questions_by_topic', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic })
      });
      const data = await res.json();
      if (data.status === 'successful') {
          cachedQuestions = data.results || [];
      }
  } catch (e) {
      cachedQuestions = [];
  }
});

// Filtrar y mostrar sugerencias
messageInput.addEventListener('input', function() {
  const value = this.value.trim().toLowerCase();
  if (!value || cachedQuestions.length === 0) {
      suggestionsDropdown.style.display = 'none';
      return;
  }
  const matches = cachedQuestions
      .filter(q => q.toLowerCase().includes(value))
      .slice(0, 5); // máximo 5 sugerencias
  if (matches.length === 0) {
      suggestionsDropdown.style.display = 'none';
      return;
  }
  suggestionsDropdown.innerHTML = matches.map((q, i) =>
      `<div class="suggestion-item${i === selectedSuggestionIndex ? ' selected' : ''}" data-index="${i}">${q}</div>`
  ).join('');
  suggestionsDropdown.style.display = 'block';
  selectedSuggestionIndex = -1;
});

// Click en sugerencia
suggestionsDropdown.addEventListener('mousedown', function(e) {
  const item = e.target.closest('.suggestion-item');
  if (item) {
      messageInput.value = item.textContent;
      suggestionsDropdown.style.display = 'none';
      messageInput.focus();
  }
});

// Navegación con teclado
messageInput.addEventListener('keydown', function(e) {
  const items = suggestionsDropdown.querySelectorAll('.suggestion-item');
  if (!items.length || suggestionsDropdown.style.display === 'none') return;
  if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex + 1) % items.length;
      updateDropdownSelection(items);
  } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedSuggestionIndex = (selectedSuggestionIndex - 1 + items.length) % items.length;
      updateDropdownSelection(items);
  } else if (e.key === 'Enter' && selectedSuggestionIndex >= 0) {
      e.preventDefault();
      messageInput.value = items[selectedSuggestionIndex].textContent;
      suggestionsDropdown.style.display = 'none';
  } else if (e.key === 'Escape') {
      suggestionsDropdown.style.display = 'none';
  }
});
function updateDropdownSelection(items) {
  items.forEach((el, i) => el.classList.toggle('selected', i === selectedSuggestionIndex));
  if (selectedSuggestionIndex >= 0) {
      items[selectedSuggestionIndex].scrollIntoView({ block: 'nearest' });
  }
}

// Ocultar sugerencias al hacer click fuera
document.addEventListener('mousedown', function(e) {
  if (!suggestionsDropdown.contains(e.target) && e.target !== messageInput) {
      suggestionsDropdown.style.display = 'none';
  }
});