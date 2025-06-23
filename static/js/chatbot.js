const { useState, useRef, useEffect } = React;
const { Send, Bot, User, BookOpen, Palette, Star, Car, Gamepad2, Trophy, Brain, Globe, Code, Cpu } = lucide;

const ChatbotFrontend = () => {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [selectedTopic, setSelectedTopic] = useState('anatomia');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const topics = [
    { value: 'anatomia', label: 'Anatomía', icon: BookOpen, color: 'bg-red-500' },
    { value: 'artes', label: 'Artes', icon: Palette, color: 'bg-purple-500' },
    { value: 'astronomia', label: 'Astronomía', icon: Star, color: 'bg-blue-500' },
    { value: 'automoviles', label: 'Automóviles', icon: Car, color: 'bg-gray-500' },
    { value: 'cultura_friki', label: 'Cultura Friki', icon: Gamepad2, color: 'bg-green-500' },
    { value: 'deportes', label: 'Deportes', icon: Trophy, color: 'bg-yellow-500' },
    { value: 'filosofia', label: 'Filosofía', icon: Brain, color: 'bg-indigo-500' },
    { value: 'geografia', label: 'Geografía', icon: Globe, color: 'bg-teal-500' },
    { value: 'programacion', label: 'Programación', icon: Code, color: 'bg-orange-500' },
    { value: 'tecnologia', label: 'Tecnología', icon: Cpu, color: 'bg-pink-500' }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async () => {
    if (!inputText.trim()) return;

    const userMessage = { text: inputText, sender: 'user', timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tema: selectedTopic,
          pregunta: inputText
        })
      });

      const data = await response.json();
      
      const botMessage = {
        text: data.respuesta,
        sender: 'bot',
        timestamp: new Date(),
        topic: selectedTopic
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        text: 'Lo siento, ocurrió un error al procesar tu pregunta.',
        sender: 'bot',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }

    setInputText('');
  };

  const getCurrentTopicIcon = () => {
    const topic = topics.find(t => t.value === selectedTopic);
    return topic ? topic.icon : BookOpen;
  };

  const getCurrentTopicColor = () => {
    const topic = topics.find(t => t.value === selectedTopic);
    return topic ? topic.color : 'bg-blue-500';
  };

  return React.createElement('div', { 
    className: "min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col" 
  },
    // Header
    React.createElement('header', { 
      className: "glass-effect border-b border-white/20 p-4" 
    },
      React.createElement('div', { 
        className: "max-w-4xl mx-auto flex items-center gap-3" 
      },
        React.createElement('div', { 
          className: `p-2 rounded-full ${getCurrentTopicColor()}` 
        },
          React.createElement(Bot, { className: "w-6 h-6 text-white" })
        ),
        React.createElement('div', null,
          React.createElement('h1', { 
            className: "text-2xl font-bold text-white" 
          }, "ChatBot Inteligente"),
          React.createElement('p', { 
            className: "text-purple-200 text-sm" 
          }, "Pregunta sobre cualquier tema")
        )
      )
    ),

    // Chat Area
    React.createElement('div', { 
      className: "flex-1 flex flex-col max-w-4xl mx-auto w-full p-4" 
    },
      React.createElement('div', { 
        className: "flex-1 glass-effect rounded-xl mb-4 overflow-hidden" 
      },
        React.createElement('div', { 
          className: "h-96 overflow-y-auto p-4 space-y-4 chat-scroll" 
        },
          messages.length === 0 && React.createElement('div', { 
            className: "text-center text-purple-300 py-8" 
          },
            React.createElement(Bot, { 
              className: "w-12 h-12 mx-auto mb-4 text-purple-400" 
            }),
            React.createElement('p', { 
              className: "text-lg mb-2" 
            }, "¡Hola! Soy tu asistente inteligente"),
            React.createElement('p', { 
              className: "text-sm" 
            }, "Selecciona un tema y hazme cualquier pregunta")
          ),
          
          messages.map((message, index) =>
            React.createElement('div', { 
              key: index, 
              className: `flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} message-appear` 
            },
              React.createElement('div', { 
                className: `max-w-xs lg:max-w-md xl:max-w-lg flex items-start gap-2 ${message.sender === 'user' ? 'flex-row-reverse' : ''}` 
              },
                React.createElement('div', { 
                  className: `p-2 rounded-full ${message.sender === 'user' ? 'bg-purple-500' : message.isError ? 'bg-red-500' : getCurrentTopicColor()}` 
                },
                  message.sender === 'user' ? 
                    React.createElement(User, { className: "w-4 h-4 text-white" }) :
                    React.createElement(Bot, { className: "w-4 h-4 text-white" })
                ),
                React.createElement('div', { 
                  className: `p-3 rounded-lg ${
                    message.sender === 'user' 
                      ? 'bg-purple-500 text-white' 
                      : message.isError 
                        ? 'bg-red-500/20 text-red-200 border border-red-500/30'
                        : 'bg-white/10 text-purple-100 border border-white/20'
                  }`
                },
                  React.createElement('p', { 
                    className: "text-sm whitespace-pre-wrap" 
                  }, message.text),
                  React.createElement('span', { 
                    className: "text-xs opacity-70 mt-1 block" 
                  },
                    message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  )
                )
              )
            )
          ),
          
          isLoading && React.createElement('div', { 
            className: "flex justify-start message-appear" 
          },
            React.createElement('div', { 
              className: "flex items-start gap-2" 
            },
              React.createElement('div', { 
                className: `p-2 rounded-full ${getCurrentTopicColor()}` 
              },
                React.createElement(Bot, { className: "w-4 h-4 text-white" })
              ),
              React.createElement('div', { 
                className: "bg-white/10 border border-white/20 p-3 rounded-lg" 
              },
                React.createElement('div', { 
                  className: "flex gap-1" 
                },
                  React.createElement('div', { 
                    className: "w-2 h-2 bg-purple-400 rounded-full loading-dot" 
                  }),
                  React.createElement('div', { 
                    className: "w-2 h-2 bg-purple-400 rounded-full loading-dot" 
                  }),
                  React.createElement('div', { 
                    className: "w-2 h-2 bg-purple-400 rounded-full loading-dot" 
                  })
                )
              )
            )
          ),
          React.createElement('div', { ref: messagesEndRef })
        )
      ),

      // Input Area
      React.createElement('div', { 
        className: "flex gap-2" 
      },
        React.createElement('select', {
          value: selectedTopic,
          onChange: (e) => setSelectedTopic(e.target.value),
          className: "glass-effect custom-select rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        },
          topics.map(topic =>
            React.createElement('option', { 
              key: topic.value, 
              value: topic.value, 
              className: "bg-slate-800 text-white" 
            },
              topic.label
            )
          )
        ),
        
        React.createElement('div', { 
          className: "flex-1 flex gap-2" 
        },
          React.createElement('input', {
            type: "text",
            value: inputText,
            onChange: (e) => setInputText(e.target.value),
            onKeyPress: (e) => e.key === 'Enter' && handleSubmit(),
            placeholder: "Escribe tu pregunta aquí...",
            className: "flex-1 glass-effect rounded-lg px-4 py-2 text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent",
            disabled: isLoading
          }),
          React.createElement('button', {
            onClick: handleSubmit,
            disabled: isLoading || !inputText.trim(),
            className: "bg-purple-500 hover:bg-purple-600 disabled:bg-purple-500/50 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors duration-200 flex items-center justify-center btn-hover"
          },
            React.createElement(Send, { className: "w-5 h-5" })
          )
        )
      ),

      // Topic Indicator
      React.createElement('div', { 
        className: "mt-2 flex items-center gap-2 text-sm text-purple-300" 
      },
        React.createElement(getCurrentTopicIcon(), { className: "w-4 h-4" }),
        React.createElement('span', null, `Tema actual: ${topics.find(t => t.value === selectedTopic)?.label}`)
      )
    )
  );
};

// Renderizar el componente
ReactDOM.render(React.createElement(ChatbotFrontend), document.getElementById('root'));