import { useState } from 'react';

interface Message {
  role: 'bot' | 'user';
  content: string;
  suggestions?: string[];
}

const INITIAL_MESSAGE: Message = {
  role: 'bot',
  content: "Hello! I'm your AI Tutor. I've analyzed your essay on Climate Change. Ask me anything about your writing — why you lost marks, how to improve specific sections, or suggestions for better vocabulary.",
  suggestions: [
    'Why did I lose marks?',
    'How can I improve my introduction?',
    'Suggest stronger vocabulary',
    'Explain my grammar errors',
  ],
};

// Mock responses for the AI tutor
const MOCK_RESPONSES: Record<string, string> = {
  'Why did I lose marks?':
    "Based on my analysis, you lost marks primarily in two areas:\n\n1. **Vocabulary (9/20)** — Your essay uses mostly basic vocabulary. Try incorporating more sophisticated terms like 'exacerbate', 'mitigate', or 'unprecedented' instead of simpler alternatives.\n\n2. **Conventions (14/20)** — There are a few grammatical issues, particularly with comma usage in compound-complex sentences. I'd recommend reviewing comma rules for dependent clauses.",
  'How can I improve my introduction?':
    "Your introduction is decent but could be stronger. Here's how to improve it:\n\n1. **Start with a hook** — Instead of diving straight into the topic, open with a striking statistic or thought-provoking question.\n\n2. **Establish context** — Briefly explain why this topic matters today.\n\n3. **Clear thesis statement** — End your intro with a strong, specific thesis that outlines your main arguments.\n\nExample: 'With global temperatures rising 1.1°C above pre-industrial levels, the urgency of addressing climate change has never been more critical.'",
  'Suggest stronger vocabulary':
    "Here are vocabulary upgrades for common words in your essay:\n\n- **'important'** → significant, paramount, pivotal\n- **'problem'** → challenge, dilemma, predicament\n- **'good'** → beneficial, advantageous, favorable\n- **'bad'** → detrimental, adverse, deleterious\n- **'use'** → utilize, employ, leverage\n- **'show'** → demonstrate, illustrate, exemplify\n\nTry replacing 3-4 basic words per paragraph with more sophisticated alternatives.",
  'Explain my grammar errors':
    "Here are the main grammar patterns I noticed:\n\n1. **Comma splices** — You're joining independent clauses with just a comma. Use a semicolon or conjunction instead.\n   - ❌ 'The climate is changing, we must act now.'\n   - ✅ 'The climate is changing; we must act now.'\n\n2. **Subject-verb agreement** — Watch for collective nouns.\n   - ❌ 'The data shows...'\n   - ✅ 'The data show...' (data is plural)\n\n3. **Pronoun clarity** — Some pronouns have ambiguous antecedents. Make sure it's clear what 'it' or 'they' refers to.",
};

export default function AITutor() {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState<'english' | 'kannada'>('english');

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    // Add user message
    const userMsg: Message = { role: 'user', content: text };

    // Generate bot response
    const response = MOCK_RESPONSES[text] ||
      `That's a great question! Based on your essay analysis, I'd suggest focusing on improving your ${
        Math.random() > 0.5 ? 'vocabulary diversity' : 'sentence structure variety'
      }. This could potentially increase your score by 5-8 points. Would you like specific examples?`;

    const botMsg: Message = { role: 'bot', content: response };

    setMessages((prev) => [...prev, userMsg, botMsg]);
    setInput('');
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSend(suggestion);
  };

  return (
    <div className="fade-in chat-container">
      {/* Header */}
      <div className="chat-header">
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>AI Essay Tutor</h2>
          <p style={{ fontSize: '0.85rem', color: '#6B7280' }}>Ask anything about your essay</p>
        </div>
        <div className="lang-toggle">
          <button
            className={language === 'english' ? 'active' : ''}
            onClick={() => setLanguage('english')}
          >
            English
          </button>
          <button
            className={language === 'kannada' ? 'active' : ''}
            onClick={() => setLanguage('kannada')}
          >
            ಕನ್ನಡ
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className="chat-message" style={msg.role === 'user' ? { flexDirection: 'row-reverse', marginLeft: 'auto' } : {}}>
            {msg.role === 'bot' && (
              <div className="chat-avatar">✦</div>
            )}
            <div>
              <div
                className="chat-bubble"
                style={msg.role === 'user' ? {
                  background: '#2D6A4F',
                  color: 'white',
                  borderTopLeftRadius: 12,
                  borderTopRightRadius: 4,
                } : {}}
              >
                {msg.content.split('\n').map((line, j) => (
                  <span key={j}>
                    {line.split(/(\*\*[^*]+\*\*)/).map((part, k) => {
                      if (part.startsWith('**') && part.endsWith('**')) {
                        return <strong key={k}>{part.slice(2, -2)}</strong>;
                      }
                      return part;
                    })}
                    {j < msg.content.split('\n').length - 1 && <br />}
                  </span>
                ))}
              </div>
              {msg.suggestions && (
                <div className="chat-suggestions">
                  {msg.suggestions.map((suggestion, j) => (
                    <button
                      key={j}
                      className="chat-suggestion"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      💡 {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <input
            type="text"
            placeholder="Ask about your essay..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend(input);
            }}
          />
          <button
            className="btn btn-primary"
            style={{ padding: '8px 16px', fontSize: '0.85rem' }}
            onClick={() => handleSend(input)}
          >
            Send
          </button>
        </div>
        <div className="chat-footer-chips">
          <span>↗ Score +5-8 possible</span>
          <span>📋 Essay context active</span>
          <span>🌐 Bilingual support</span>
        </div>
      </div>
    </div>
  );
}
