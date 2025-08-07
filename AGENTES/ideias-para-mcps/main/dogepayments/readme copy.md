## O problema que o DogePay Crypto Payments resolve - Integração com DREX

Pagamentos online alimentados por criptomoeda são essenciais para tornar a criptomoeda popular. No entanto, a maioria das empresas SaaS bem-sucedidas dependem do modelo de negócios de pagamentos recorrentes, o que não é possível atualmente. Há benefícios tanto para os comerciantes que usam o DogePay quanto para os clientes que pagam com o DogePay.

### Benefícios para comerciantes
- É difícil configurar um gateway de pagamentos. Com a presença de uma API, uma React Library e páginas de pagamento hospedadas, as empresas de SaaS podem integrar facilmente o DogePay para tornar a experiência de seus usuários perfeita, em menos de 10 linhas de código.
- Pagamentos recorrentes são extremamente raros com os gateways de criptomoedas existentes, e o DogePay suporta essa funcionalidade.
- Pagamentos com cartão de crédito custam aos comerciantes altas taxas de processamento. Aceitar pagamentos com DogePay significa que eles não precisam pagar essas taxas.
- Criadores de conteúdo e desenvolvedores de código aberto podem aceitar doações usando seu link de doação exclusivo.
- Ao aceitar pagamentos com cartão de crédito, os vendedores ficam vulneráveis a chargebacks, o que pode ser extremamente prejudicial, pois eles incorrem em perdas. Com pagamentos em criptomoeda, eles não precisam se preocupar com chargebacks.

### Benefícios para os usuários
- Os gateways de pagamento cripto que suportam pagamentos recorrentes exigem que o dinheiro seja mantido com o processador de pagamento. O DogePay oferece uma solução em que o cliente mantém seu próprio dinheiro e o vendedor pode aceitar pagamentos cripto recorrentes.
- Quando os usuários pagam um fornecedor com seu cartão de crédito, o gateway de pagamento armazena essas informações mesmo que o pagamento não seja recorrente. Isso os torna extremamente vulneráveis a vazamentos de dados. Com o DogePay, apenas o endereço da carteira pública é armazenado, o que não pode ser usado para acessar fundos.
- Muitas vezes, os usuários esquecem de cancelar assinaturas e acabam sendo cobrados automaticamente. Com as faturas inteligentes do DogePay, eles nunca serão cobrados a menos que queiram fazer as transações.

## Desafios que enfrentamos

Nós três somos absolutamente novos no espaço web3 e decidimos aprender a tecnologia na hora enquanto desenvolvíamos o dApp. Como éramos novos, encontramos muitos desafios, mas conseguimos resolver a maioria deles. Alguns dos principais desafios foram:

### Documentação Limitada
Como web3 e Moralis são plataformas relativamente novas, a documentação e o suporte do fórum online eram bem limitados, especialmente para React. Aprendemos ao longo do caminho usando muita tentativa e erro, bem como depuração constante.

### Configuração do CRON
Ao implementar nossas faturas inteligentes baseadas em CRON, configurar o cron foi um grande desafio porque tínhamos que garantir que ele fosse configurado de forma confiável e que voltasse a funcionar automaticamente. Também testávamos diariamente se as faturas estavam sendo enviadas corretamente. Isso levou quase uma semana de testes.

### Problemas com Netlify e Heroku
Decidimos hospedar nosso dApp web3 no Netlify e Heroku. Durante os testes, percebemos que, embora o código estivesse funcionando no localhost, ele não funcionava no Netlify. Migramos para o Heroku, mas também não funcionou. O erro provavelmente foi causado por bibliotecas incompatíveis ou firewalls que impediram o tráfego de rede da transação assinada.

Decidimos mudar para o Google Cloud Platform e criar uma máquina virtual Linux CentOS 8 barebone para implantar nosso aplicativo. A máquina virtual nos deu controle total do ambiente e das configurações do firewall, e o aplicativo funcionou com sucesso no Google Cloud.

### Problemas com API e Biblioteca
Ao construir a biblioteca de React do DogePay e a API, tivemos que garantir que nosso código fosse modular, de forma que o mesmo código pudesse ser usado para alimentar a API, a biblioteca e o próprio painel. Isso foi extremamente desafiador, mas conseguimos projetar nosso aplicativo de forma modular.

---

## Arquitetura do DogePay

O DogePay foi projetado para ser um sistema modular e escalável, com uma arquitetura distribuída baseada em microserviços. Abaixo está um resumo da estrutura do sistema:

### 1. **Camada de Interface do Usuário (Frontend)**
- Aplicação desenvolvida em **React.js** para proporcionar uma experiência interativa e responsiva.
- Integração com a **React Library** do DogePay para facilitar a incorporação de pagamentos em aplicações SaaS.
- Páginas de pagamento hospedadas para empresas que não querem desenvolver uma integração personalizada.

### 2. **Camada de API e Backend**
- Desenvolvido em **Node.js com Express**, garantindo alto desempenho e escalabilidade.
- API RESTful para comunicação com clientes e serviços internos.
- Banco de dados **PostgreSQL** para armazenar dados de usuários, transações e assinaturas.
- Armazenamento de chaves criptográficas e autenticação usando **OAuth 2.0 e JWT**.

### 3. **Serviço de Pagamentos**
- Conectado à blockchain é uma solução de pagamentos que opera na blockchain Polygon PoS (Proof-of-Stake). Essa escolha permite que as taxas de GAS sejam baixas, mantendo as transações seguras  para processar pagamentos e confirmar transações.
- Uso de **WebSockets** para notificar os usuários sobre o status das transações em tempo real.
- Suporte a pagamentos recorrentes através de **contratos inteligentes** e faturas programadas.

### 4. **Mecanismo de Faturas Inteligentes**
- Serviço baseado em **CRON Jobs** para geração e envio automático de faturas.
- API para permitir que os comerciantes consultem e gerenciem assinaturas.
- Notificações via **Webhooks** para integração com sistemas terceiros.

### 5. **Infraestrutura e Hospedagem**
- Hospedado no **Google Cloud Platform**, utilizando **máquinas virtuais Linux CentOS 8**.
- Uso de **Docker** e **Kubernetes** para garantir escalabilidade e manutenção simplificada.
- Balanceamento de carga e CDN para otimizar a entrega de conteúdo globalmente.

### 6. **Segurança e Compliance**
- Proteção contra ataques **DDoS** e uso de **firewalls avançados**.
- Armazenamento seguro de informações sensíveis com **criptografia AES-256**.
- Monitoramento de atividades suspeitas utilizando **logs centralizados e análise de padrões anômalos**.

O DogePay é uma solução inovadora que permite pagamentos cripto recorrentes, eliminando taxas abusivas e oferecendo uma experiência segura tanto para comerciantes quanto para clientes. Seu design modular garante flexibilidade e escalabilidade para o futuro do comércio digital.

