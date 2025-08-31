### **Plano de Ação Proposto**

#### **1. Entendimento do Projeto**
O objetivo é criar um sistema de gestão de investimentos (Ações e Fundos Imobiliários) que utiliza uma arquitetura de agentes de IA (LLM) para automatizar cálculos, buscar dados e gerar relatórios.

#### **2. Funcionalidades Essenciais (Features)**
* **Cálculos de Métricas:** Dividend Yield, Total de Dividendos, Preço Médio, Retorno Financeiro.
* **Dados em Tempo Real:** Integração para buscar cotações atuais (similar ao `googlefinance`).
* **Relatórios e Sumários:**
    * Valor total investido (separado por Ações e FIIs, e agrupado por setor).
    * Resumo de dividendos (rentabilidade mensal e anual).

#### **3. Análise da Arquitetura e Stack Tecnológica**
* **Linguagem:** Você sugeriu Ruby on Rails. É uma excelente framework para aplicações web. No entanto, o ecossistema de IA (LangChain, LangGraph, bibliotecas para modelos LLM como Gemini e Ollama) é imensamente mais maduro e robusto em **Python**. Para um projeto onde os agentes de IA são o núcleo, recomendo fortemente o uso de **Python** para o backend, possivelmente com um framework como FastAPI ou Django. **Minha sugestão é prosseguir com Python.**
* **Agentes de IA (LangChain/LangGraph):** A arquitetura será modular e escalável. Proponho a criação dos seguintes agentes iniciais:
    * **`MarketDataAgent`:** Responsável por se conectar a APIs (como a do Google Finance ou outras APIs financeiras) para buscar preços de ativos em tempo real.
    * **`PortfolioCalculatorAgent`:** Recebe os dados do portfólio e os dados de mercado para realizar todos os cálculos financeiros (preço médio, dividend yield, etc.).
    * **`DatabaseAgent`:** Responsável por toda a interação com o banco de dados (CRUD de ativos, transações, dividendos). Garante a persistência dos dados.
    * **`ReportingAgent`:** Gera os sumários e relatórios consolidados (por setor, por período, etc.), utilizando os dados processados pelos outros agentes.
    * **`OrchestratorAgent` (usando LangGraph):** O cérebro da operação. Ele recebe a requisição do usuário (ex: "Calcular meu resumo de dividendos de Maio"), entende a intenção, e coordena os outros agentes na sequência correta para cumprir a tarefa.
* **Modelos de LLM:** A arquitetura permitirá a conexão com diferentes provedores de LLM, como a API do Google Gemini e uma instância local do Ollama, através de abstrações do LangChain.
* **Banco de Dados:** Para armazenar transações, informações de ativos e dividendos, um banco de dados relacional é ideal. **PostgreSQL** é uma excelente escolha por sua robustez, escalabilidade e ótima integração com Python. É a minha recomendação.
* **Contêineres:** **Docker** e **Docker Compose** serão usados para orquestrar a aplicação, o banco de dados (PostgreSQL) e qualquer outro serviço necessário, garantindo um ambiente de desenvolvimento e produção consistente e fácil de configurar.

#### **4. Fases do Projeto**
Proponho dividir o desenvolvimento inicial nas seguintes macro-etapas:
1.  **Fase 1: Fundação e Configuração do Ambiente:** Criação da estrutura do projeto, configuração do Docker Compose (Python App, PostgreSQL).
2.  **Fase 2: Modelagem do Domínio e Banco de Dados:** Definição e implementação das tabelas principais (Ativos, Transações, Dividendos).
3.  **Fase 3: Implementação dos Agentes Nucleares:** Desenvolvimento dos agentes `MarketDataAgent`, `DatabaseAgent` e `PortfolioCalculatorAgent`.
4.  **Fase 4: Orquestração e Lógica de Negócio:** Criação do `OrchestratorAgent` com LangGraph para conectar os fluxos de trabalho.
5.  **Fase 5: Relatórios e API:** Desenvolvimento do `ReportingAgent` e exposição dos resultados através de uma API.
