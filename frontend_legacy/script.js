const API_BASE_URL = "https://chatbot-triagem-medica.onrender.com/api/v1";
// const API_BASE_URL = "http://127.0.0.1:8001/api/v1";

// --- Variáveis Globais de estado ---
let currentStep = 'welcome'; // As próximas são: 'lgpd', 'ask_name', 'ask_address', 'ask_age', 'smartwatch_loading', 'gemini_chat', 'final_display'
let sessionId = null; // Busca do back e salva
let personalData = {
  nome_completo: '',
  endereco: '',
  idade: 0
};
let fichaDeAtendimento = {};
let conversationIsOver = false;

// --- Referências aos Elementos do DOM ---
const chatMessagesDiv = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendMessageButton = document.getElementById('sendMessageButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const dataCollectionFormDiv = document.getElementById('dataCollectionForm');
const personalDataForm = document.getElementById('personalDataForm');
const finalFichaContainer = document.getElementById('finalFichaContainer');
const fichaContentPre = document.getElementById('fichaContent');
const fichaContentFormattedDiv = document.getElementById(
  "fichaContentFormatted"
);
const chatInputArea = document.getElementById('chatInputArea');

// Inputs do formulário
const inputNomeCompleto = document.getElementById('nome_completo');
const inputEndereco = document.getElementById('endereco');
const inputIdade = document.getElementById('idade');
const errorNomeCompleto = document.getElementById('errorNomeCompleto');
const errorEndereco = document.getElementById('errorEndereco');
const errorIdade = document.getElementById('errorIdade');

// --- Funções Auxiliares de UI ---
/**
 * Adiciona uma mensagem ao chat.
 * @param {'bot'|'user'} sender - Quem está enviando a mensagem.
 * @param {string} text - Texto da mensagem.
 */
function addMessage(sender, text) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message-bubble');
    if (sender === 'bot') {
        messageDiv.classList.add('message-bot');
    } else {
        messageDiv.classList.add('message-user');
    }
    messageDiv.textContent = text;
    chatMessagesDiv.appendChild(messageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    chatMessagesDiv.scrollTop = chatMessagesDiv.scrollHeight;
}

function showLoading() {
    loadingSpinner.classList.remove('hidden');
    chatInputArea.classList.add('hidden'); // Esconde a área de input enquanto carrega
}

function hideLoading() {
    loadingSpinner.classList.add('hidden');
    if (!conversationIsOver && currentStep !== 'final_display') { // Só mostra o input se a conversa não acabou
        chatInputArea.classList.remove('hidden');
    }
}

function showDataCollectionForm() {
    dataCollectionFormDiv.classList.remove('hidden');
    chatInputArea.classList.add('hidden'); // Esconde a área de input do chat
}

function hideDataCollectionForm() {
    dataCollectionFormDiv.classList.add('hidden');
}

function showFinalFicha() {
    finalFichaContainer.classList.remove('hidden');
    chatInputArea.classList.add('hidden'); // Garante que o input do chat esteja oculto
    // Opcional: Limpar mensagens antigas se for uma "nova tela"
    // chatMessagesDiv.innerHTML = '';
}

/**
 * Formata o objeto fichaDeAtendimento para exibição amigável.
 * @param {object} ficha O objeto fichaDeAtendimento completo.
 * @returns {string} O HTML formatado para exibição.
 */
function formatFichaForDisplay(ficha) {
  let htmlContent = '';

  // Dados Pessoais
  htmlContent += `<div class="ficha-item"><strong>Nome Completo:</strong> ${ficha.nome_completo || 'N/A'}</div>`;
  htmlContent += `<div class="ficha-item"><strong>Endereço:</strong> ${ficha.endereco || 'N/A'}</div>`;
  htmlContent += `<div class="ficha-item"><strong>Idade:</strong> ${ficha.idade || 'N/A'} anos</div>`;

  // Dados do Smartwatch (Fisiológicos)
  if (ficha.dados_fisiologicos) {
      htmlContent += `<div class="ficha-item"><strong>Dados do Smartwatch:</strong></div>`;
      htmlContent += `<ul>`;
      htmlContent += `<li class="ficha-item">Altura: ${ficha.dados_fisiologicos.altura_cm || 'N/A'} cm</li>`;
      htmlContent += `<li class="ficha-item">Peso: ${ficha.dados_fisiologicos.peso_kg || 'N/A'} kg</li>`;
      htmlContent += `<li class="ficha-item">Pressão Arterial: ${ficha.dados_fisiologicos.pressao_arterial_sistolica || 'N/A'}/${ficha.dados_fisiologicos.pressao_arterial_diastolica || 'N/A'} mmHg</li>`;
      htmlContent += `<li class="ficha-item">Oxigenação: ${ficha.dados_fisiologicos.oxigenacao_sangue_percentual || 'N/A'}%</li>`;
      htmlContent += `<li class="ficha-item">Nível de Estresse: ${ficha.dados_fisiologicos.nivel_estresse || 'N/A'}</li>`;
      htmlContent += `</ul>`;
  } else {
      htmlContent += `<div class="ficha-item"><strong>Dados do Smartwatch:</strong> Não disponíveis</div>`;
  }

  // Especialidade e Orientação
  htmlContent += `<div class="ficha-item"><strong>Especialidade Sugerida:</strong> ${ficha.especialidade_medica || 'N/A'}</div><br />`;
  htmlContent += `<div class="ficha-item"><strong>Orientação ao Médico:</strong> ${ficha.orientacao_ao_medico || 'N/A'}</div>`;

  return htmlContent;
}

// --- Funções de Comunicação com o Backend ---
async function iniciarAtendimento(pacienteData) {
  try {
    showLoading();
    const response = await fetch(
      `${API_BASE_URL}/iniciar_atendimento`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(pacienteData),
      }
    );
    const result = await response.json();
    if (response.ok) {
      sessionId = result.session_id;
      fichaDeAtendimento = { ...pacienteData, session_id: sessionId };
      hideLoading();
      addMessage(
        "bot",
        "Dados pessoais recebidos! Agora vamos recolher dados do seu smartwatch..."
      );
      currentStep = "smartwatch_loading";
      processStep(); // Avança para o próximo passo
    } else {
      throw new Error(result.detail || "Erro ao iniciar atendimento.");
    }
  } catch (error) {
    hideLoading();
    addMessage(
      "bot",
      `Ocorreu um erro ao iniciar o atendimento: ${error.message}. Por favor, tente novamente.`
    );
    console.error("Erro ao iniciar atendimento:", error);
    // Permite tentar novamente o passo de coleta de dados
    currentStep = "ask_age"; // Volta para o último passo de coleta para re-tentar
    showDataCollectionForm(); // Re-exibe o formulário
  }
}

async function obterDadosSmartwatch() {
  try {
    showLoading();
    const response = await fetch(
      `${API_BASE_URL}/obter_dados_smartwatch/${sessionId}`
    );
    const result = await response.json();
    if (response.ok) {
      fichaDeAtendimento = {
        ...fichaDeAtendimento,
        dados_fisiologicos: result.dados_fisiologicos,
      };
      hideLoading();
      addMessage("bot", "Dados fisiológicos coletados com sucesso!");
      addMessage(
        "bot",
        "Pronto! Agora me diga a sua queixa principal. Seja o mais detalhado possível."
      );
      currentStep = "gemini_chat"; // Entra no modo de chat com Gemini
      chatInputArea.classList.remove("hidden"); // Garante que o input está visível
    } else {
      throw new Error(
        result.detail || "Erro ao obter dados do smartwatch."
      );
    }
  } catch (error) {
    hideLoading();
    addMessage(
      "bot",
      `Ocorreu um erro ao obter dados do smartwatch: ${error.message}. Por favor, tente novamente.`
    );
    console.error("Erro ao obter dados smartwatch:", error);
    // Se der erro, pode pedir para o usuário tentar novamente ou pular
    addMessage(
      "bot",
      "Não foi possível coletar os dados do smartwatch. Vamos prosseguir com a queixa principal."
    );
    currentStep = "gemini_chat";
    chatInputArea.classList.remove("hidden");
  }
}

async function chatWithGemini(userMessage) {
  try {
    showLoading();
    const response = await fetch(`${API_BASE_URL}/chat_with_gemini`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_message: userMessage,
      }),
    });
    const result = await response.json(); // result é ChatGeminiResponse

    if (response.ok) {
      hideLoading();
      addMessage("bot", result.bot_message);

      if (result.status === "final") {
        conversationIsOver = true;
        fichaDeAtendimento = result.ficha_de_atendimento; // A ficha completa vem aqui
        addMessage(
          "bot",
          "Acabou, vamos exibir a ficha de atendimento para o médico."
        );
        currentStep = "final_display";
        processStep(); // Avança para a tela final
      }
      // Se status for 'ongoing', a conversa continua, e o input do chat já está visível
    } else {
      throw new Error(result.detail || "Erro na comunicação com a IA.");
    }
  } catch (error) {
    hideLoading();
    addMessage(
      "bot",
      `Ocorreu um erro na comunicação com a IA: ${error.message}. Por favor, tente novamente.`
    );
    console.error("Erro ao conversar com Gemini:", error);
    // Permite ao usuário tentar novamente ou continuar
    chatInputArea.classList.remove("hidden");
  }
}

async function obterFichaCompletaParaDisplay() {
  try {
    // Embora a ficha já venha no chatWithGemini final, este endpoint garante que
    // podemos buscar a ficha a qualquer momento se necessário para a tela final.
    const response = await fetch(
      `${API_BASE_URL}/obter_ficha_completa/${sessionId}`
    );
    const result = await response.json();
    if (response.ok) {
      fichaContentPre.textContent = JSON.stringify(
        result.ficha_de_atendimento,
        null,
        2
      );
    } else {
      throw new Error(result.detail || "Erro ao obter ficha completa.");
    }
  } catch (error) {
    fichaContentPre.textContent = `Erro ao carregar a ficha: ${error.message}`;
    console.error("Erro ao obter ficha completa para display:", error);
  }
}

// --- Lógica Principal do Fluxo Conversacional ---
function processStep() {
  switch (currentStep) {
    case "welcome":
      addMessage(
        "bot",
        "Olá! Seja bem-vindo(a) ao Centro de Atendimento Médico Remoto! Por favor, leia com atenção."
      );
      setTimeout(() => {
        currentStep = "lgpd";
        processStep();
      }, 3000);
      break;
    case "lgpd":
      addMessage(
        "bot",
        "Seus dados serão coletados e tratados com a máxima confidencialidade e segurança, em conformidade com a Lei Geral de Proteção de Dados (LGPD). Ao prosseguir, você concorda com o uso de suas informações para fins de triagem médica e apoio ao diagnóstico. Seus dados não serão compartilhados com terceiros sem seu consentimento explícito, exceto conforme exigido por lei."
      );
      setTimeout(() => {
        currentStep = "ask_name";
        processStep();
      }, 5000);
      break;
    case "ask_name":
      addMessage("bot", "Qual é o seu nome completo?");
      chatInputArea.classList.remove("hidden"); // Garante que o input esteja visível
      messageInput.focus();
      break;
    case "ask_address":
      addMessage("bot", "Qual é o seu endereço?");
      messageInput.focus();
      break;
    case "ask_age":
      addMessage("bot", "Qual é a sua idade?");
      messageInput.focus();
      break;
    case "init_backend":
      // Este passo é acionado por handleUserInput após coletar a idade
      hideDataCollectionForm(); // Esconde o formulário de coleta
      iniciarAtendimento(personalData); // Chama a API para iniciar atendimento
      break;
    case "smartwatch_loading":
      // Este passo é acionado por iniciarAtendimento
      obterDadosSmartwatch(); // Chama a API para obter dados do smartwatch
      break;
    case "gemini_chat":
      // Este passo é o modo de chat livre com o Gemini, esperando input do usuário.
      // A primeira mensagem já foi adicionada por obterDadosSmartwatch.
      messageInput.focus();
      break;
    case "final_display":
      showFinalFicha(); // Mostra a área da ficha final
      // fichaContentPre.textContent = JSON.stringify(
      //   fichaDeAtendimento,
      //   null,
      //   2
      // );
      fichaContentFormattedDiv.innerHTML =
        formatFichaForDisplay(fichaDeAtendimento);
      break;
  }
}

function handleUserInput(event) {
  if (event.type === "click" || event.key === "Enter") {
    const userMessage = messageInput.value.trim();
    if (userMessage === "") return;

    addMessage("user", userMessage);
    messageInput.value = ""; // Limpa o input

    // Lógica para cada passo da conversa
    if (currentStep === "ask_name") {
      personalData.nome_completo = userMessage;
      currentStep = "ask_address";
      processStep();
    } else if (currentStep === "ask_address") {
      personalData.endereco = userMessage;
      currentStep = "ask_age";
      processStep();
    } else if (currentStep === "ask_age") {
      const age = parseInt(userMessage);
      if (isNaN(age) || age < 0 || age > 120) {
        addMessage(
          "bot",
          "Por favor, digite uma idade válida (número entre 0 e 120)."
        );
        // Permanece no 'ask_age'
      } else {
        personalData.idade = age;
        currentStep = "init_backend";
        processStep();
      }
    } else if (currentStep === "gemini_chat") {
      chatWithGemini(userMessage);
    }
  }
}

// --- Event Listeners ---
sendMessageButton.addEventListener("click", handleUserInput);
messageInput.addEventListener("keypress", handleUserInput);

// Lidar com o envio do formulário de dados pessoais
personalDataForm.addEventListener("submit", function (event) {
  event.preventDefault(); // Previne o recarregamento da página

  // Validação básica do formulário
  let isValid = true;
  errorNomeCompleto.classList.add("hidden");
  errorEndereco.classList.add("hidden");
  errorIdade.classList.add("hidden");

  if (inputNomeCompleto.value.trim() === "") {
    errorNomeCompleto.classList.remove("hidden");
    isValid = false;
  }
  if (inputEndereco.value.trim() === "") {
    errorEndereco.classList.remove("hidden");
    isValid = false;
  }
  const idadeValue = parseInt(inputIdade.value);
  if (isNaN(idadeValue) || idadeValue < 0 || idadeValue > 120) {
    errorIdade.classList.remove("hidden");
    isValid = false;
  }

  if (isValid) {
    personalData.nome_completo = inputNomeCompleto.value.trim();
    personalData.endereco = inputEndereco.value.trim();
    personalData.idade = idadeValue;
    currentStep = "init_backend"; // Define o próximo passo para iniciar o backend
    processStep(); // Processa o próximo passo
  } else {
    addMessage(
      "bot",
      "Por favor, preencha todos os campos corretamente para prosseguir."
    );
  }
});

// Inicia a conversa quando a página é carregada
window.onload = processStep;