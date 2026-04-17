# Memória Técnica: Sistema de Triagem em Telemedicina Assistiva (PIBIC 2024-2026)

## 1. Visão Geral e Propósito Científico
Este projeto materializa os achados da Revisão Sistemática de Literatura (PIBIC 24-25) em um Produto Mínimo Viável (PIBIC 25-26). O sistema atua como uma "clínica miniaturizada" para comunidades com baixa permeabilidade urbana, mitigando as dificuldades de acesso aos serviços de saúde essenciais (ODS 3.8 da ONU).

O núcleo do sistema é a integração de **Tecnologias Assistivas (Smartwatches e Smartphones)** orquestradas por **Inteligência Artificial Generativa** para conduzir a anamnese inicial e triagem de pacientes, enviando um screening estruturado para o médico.

## 2. Topologia da Arquitetura (Edge/Cloud)
A solução adota uma arquitetura orientada a eventos e microsserviços, alinhada com as restrições de latência e disponibilidade de hardware em ambientes clínicos restritos.

* **API Gateway (FastAPI):** Porta de entrada síncrona. Gerencia sessões (UUID), recebe os dados biométricos e expõe endpoints REST.
* **Mensageria (RabbitMQ 3.12):** Desacopla o gateway da inferência de IA. Garante entrega (ACK/NACK) e implementa Dead Letter Queues (DLQs) para resiliência.
* **State & Cache (Redis 7):** Gerencia o status dos jobs assíncronos (PENDING -> PROCESSING -> COMPLETED) e previne requisições duplicadas (idempotência).
* **Persistência (PostgreSQL + SQLAlchemy):** Armazena de forma persistente e segura as sessões, dados fisiológicos e transcrições das consultas.
* **AI Workers (Consumidores):**
    * *Gemini Module:* Endpoint focado em manter o contexto da conversa e gerar o JSON estruturado da anamnese.
    * *Nemotron Service:* Worker assíncrono projetado para operar com hardware local (GPU/CUDA via Transformers) ou delegar para a API da NVIDIA (APIWorker) como fallback de infraestrutura.

## 3. Fluxo de Dados e Endpoints Principais
O fluxo do paciente foi mapeado a partir dos protótipos em Figma e implementado nos seguintes contratos:

1.  **Sessão:** `POST /api/v1/iniciar_atendimento` -> Cria UUID, recebe demografia.
2.  **Sensores:** `GET /api/v1/obter_dados_smartwatch/{session_id}` -> (Atualmente Simulado) Coleta Altura, Peso, PAS/PAD, SpO2 (Saturação de Oxigênio) e Nível de Estresse.
3.  **Chat/Anamnese:** `POST /api/v1/chat_with_gemini` -> Processa a queixa. O modelo atua sob um prompt estrito para retornar `status: ongoing` ou `status: final` (com a especialidade sugerida).
4.  **Processamento NLP Extra:** `POST /chat?mode={auto|gpu|api}` -> Aciona o worker assíncrono do Nemotron via mensageria.

## 4. Constraints Críticas de Negócio e Segurança
1.  **Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018):** O armazenamento dos dados fisiológicos do gêmeo digital (Personal Digital Twin - PDT) requer rigor na anonimização e trânsito seguro em banco.
2.  **Formato Estrito da IA:** A IA (Gemini/Nemotron) é instruída para **nunca** dar o diagnóstico médico final, mas atuar como atendente de triagem. A saída da inferência deve ser rigorosamente um JSON estruturado; blocos de Markdown acidentais devem ser sanitizados pelo backend.
3.  **Hardware Fallback (O "Exagero" Controlado):** O escopo acadêmico prevê processamento LLM na borda (Edge GPU). Na prática de desenvolvimento, o sistema detecta a ausência de CUDA disponível (ex: rodando em CPU i5/Ryzen) e roteia a requisição automaticamente para o `APIWorker` da NVIDIA, preservando a integridade do sistema.

## 5. Próximos Passos (Roadmap de Desenvolvimento)
* **[Pendente]** Migrar a memória em cache da sessão de chat do Gemini para o PostgreSQL usando SQLAlchemy.
* **[Pendente]** Consolidar a interface frontend (React/Flutter) consumindo os endpoints consolidados do novo API Gateway.
* **[Pendente]** Substituir a simulação de hardware por coleta real via APIs de saúde mobile (ex: Samsung Health) conforme documentado no artigo base.