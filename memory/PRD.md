# PRD — donas-projector-pcma-cebaspe-002

## Overview
Existing project cloned from GitHub (https://github.com/cicijevaira-sys/donas-projector-pcma-cebaspe-002)
and configured in the Emergent sandbox (/app). Public inscription/tracking site (Cebraspe / PCMA concurso)
with an admin panel for tracking, inscriptions, dashboard KPIs and PIX config.

## Stack
- Backend: FastAPI (Python) — /app/backend (server.py + admin_routes.py + pix_generator.py)
- Frontend: React CRA (craco) — /app/frontend
- DB: MongoDB (MONGO_URL / DB_NAME from /app/backend/.env — unchanged)

## Setup done (2026-06 / clone date 2026-08-25 in sandbox)
- Cloned repo into /app, preserving .git, .emergent, backend/.env, frontend/.env
- Backend deps installed (requirements.txt; emergentintegrations not present — no skip needed). Extras bcrypt/Pillow/qrcode[pil] already satisfied.
- Frontend deps installed via yarn
- Seeded admin `farpa` (bcrypt) into `admins` collection
- Services restarted via supervisor (backend + frontend)

## Key routes
- GET /api/ -> health ({"message":"Painel Administrativo API"})
- POST /api/admin/auth/login -> returns JWT { token, user }
- Admin UI SPA route: /farpapainel

## Validation status (passed)
- GET /api/ -> 200
- Frontend root -> 200, renders concurso landing page
- POST /api/admin/auth/login {farpa/Ads102030} -> JWT returned

## Notes
- Preview serves frontend via hot-reload dev server; production `yarn build` not required for preview.
- JWT_SECRET defaults to 'change-me' (env-overridable). Consider setting ADMIN/JWT env in production.

## Regras do concurso SESAU_AL_26 (memorizar)
- Taxa de inscrição: Nível SUPERIOR (Especialista, cargos 01-12) = R$ 160,00 | Nível MÉDIO (Assistente, cargos 13-15) = R$ 120,00
- Estes valores estão nos data-price das options do #VAGA em dados-inscricao.html e alimentam a geração do pagamento (PIX).
- Localidade de Vaga: CARGO 1 (Biologia) -> só Maceió; CARGO 2-15 -> Arapiraca, Delmiro Gouveia, Maceió, Palmeira dos Índios, Porto Calvo, União dos Palmares.
- Local de prova: estado Alagoas/AL (fixo); municípios Arapiraca/AL e Maceió/AL.
- Período de inscrições: 20/07/2026 a 26/08/2026 às 23:59.

## Rebrand completo PC_MA_26 -> SESAU_AL_26 (todas as telas)
Data: sessão de migração.
Páginas públicas (7) migradas: inicio.html, termos.html, inscricao.html, dados-inscricao.html, confirmacao.html, inscricao-realizada.html, pagamento-pix.html (tela + documento de impressão).
Painel admin (/donaspainel) rebrandeado: bundle main.fda9cfa5.js ('Concurso PC MA 26' -> 'Concurso SESAU AL 26'), index.html title, donaspainel-documentos.html title ('Polícia Penal RN' -> 'Documentos - Painel Cebraspe').
Backend (admin_routes.py): PIX defaults pix_nome='CONCURSO ALAGOAS', pix_cidade='MACEIO AL'; telegram_titulo fallback 'NOVA INSCRIÇÃO - SESAU AL 26'; fallbacks 'IDECAN'->'CONCURSO ALAGOAS', 'BELO HORIZONTE'->'MACEIO AL'.
DB settings corrigidas: pix_cidade 'Marceio AL' -> 'MACEIO AL'.
Regras: taxa superior (cargos 01-12) R$160,00; médio (13-15) R$120,00. Localidade de Vaga: CARGO 1 só Maceió; demais 6 cidades. Local de prova AL (Arapiraca/Maceió).
Identificadores JS internos window.IdecanNotice/IdecanConfirm mantidos (nomes internos, não visíveis ao usuário).
Verificado por testing_agent (iterations 10-13): 100% backend e frontend.
Pendências/observações: imagem decorativa do login do painel (Tartaruga Ninja) é um asset off-brand — aguardando decisão do usuário para trocar.

## Change log — 2026-06 (Rebrand to Instituto AOCP)
- User request: rebrand entire public site from Cebraspe/SEAP-MA to Instituto AOCP + concurso SAEB Bahia (Polícia Civil, 750 vagas: Delegado 100, Escrivão 150, Investigador 500).
- DONE (homepage first, per user): replaced /app/frontend/public/inicio.html with the user-provided Instituto AOCP homepage (self-contained: inline Tailwind CSS + base64 images). Adjustments: removed CSP meta (was blocking /api fetch), removed external canonical, repointed "Formulário de Solicitação de Inscrição" link -> /dados-inscricao.html, injected /api/track/access tracker, appended </body></html>.
- Registration fees agreed for next phase: Delegado R$ 220,00 | Escrivão R$ 190,00 | Investigador R$ 190,00.
- PENDING (next): adapt registration flow (edital pages, dados-inscricao, inscricao, confirmacao, pagamento-pix) + admin panel to SAEB Bahia / 3 cargos + fees; add salaries later.

## Change log — 2026-06 (Header exato AOCP + Cargos SAEB)
- Cabeçalho do fluxo: recortado EXATO do arquivo AOCP do usuário e injetado via Shadow DOM (CSS original isolado). Arquivo: /app/frontend/public/aocp-header.v3.js (versionado p/ furar cache). Inclui logo instituto aocp, botão SAIR verde #37a87f, e faixa-sombra (elemento real com gradiente) como divisão header/página. Aplicado nas 6 páginas do fluxo (script src=/aocp-header.v3.js). Página de referência: /app/frontend/public/modelo-aocp.html.
- Card do Edital SAEB (barra cinza + logo Governo BA + texto 750 vagas) no topo de inscricao.html e dados-inscricao.html. Título "Formulário de Inscrição" movido para abaixo do card. Container .Miolo alargado p/ 1280px/24px (alinhado ao header).
- CARGOS (dados-inscricao.html): concurso único SAEB com 3 cargos e taxas -> Delegado R$220,00 (01), Escrivão R$190,00 (02), Investigador R$190,00 (03). Dropdown VAGA popula direto (tipo fixo '1'). Valor via data-price -> flui p/ confirmacao/pagamento-pix. Local de prova: Bahia/BA, Salvador/BA.

## Change log — Painel Admin (/donaspainel) rebrand
- Painel SPA em frontend/public/donaspainel/ (index.html + static/js/main.*.js + admin-extras.js + documentos.html). Substituído tudo do projeto antigo: "Concurso SEAP MA 26"->"Concurso SAEB BA", "EDITAL 001/2026"->"EDITAL 002/2026", placeholder pix "SAO LUIS MA"->"SALVADOR", "Painel Cebraspe"/"Cebraspe"->"Instituto AOCP". Aplicado em login, dashboard, header, relatório e title da aba.
- Telegram: default _build_telegram_message titulo = 'NOVA INSCRIÇÃO - SAEB BA 26'; DB settings.main.telegram_titulo atualizado para o mesmo. PIX no DB: pix_nome='CONCURSO SAEB BA', pix_cidade='SALVADOR'.
- PENDENTE opcional: imagem de fundo do login (tartaruga ninja/donatelo) é placeholder antigo; trocar por algo institucional quando o usuário quiser.

## Update 2026-06 (fork) — Mobile header fix on inicio.html
- FIXED: mobile header was missing on inicio.html. Root cause: the mobile navbar block had SingleFile's `.sf-hidden{display:none!important}` class forcing it hidden on all screens, AND the drawer top-bar (hamburger + logo) had been stripped, leaving only the drawer-side menu.
- Rebuilt mobile block as a daisyUI drawer (lg:hidden): drawer-toggle input (visually hidden), drawer-content bar with hamburger button (three-line svg) + Instituto AOCP logo (same base64 as desktop), and drawer-side menu (Início, Quem Somos, Concursos▾, Peça seu Certificado, Projetos Sociais, Cursos Livres, Notícias, Contato▾).
- Verified via mobile-width (390px) screenshots: closed header matches original print; hamburger opens the full menu.
- Note: static HTML is heavily browser-cached — users must Ctrl+Shift+R.

## Remaining / backlog
- P2: Admin login page (/donaspainel) still shows a placeholder background image.
- P1: Add form fields "Local de lotação — 1 - ESTADO DA BAHIA" and single "Local de prova: SALVADOR/BA".

## Update 2026-06 (fork) — Links/Publicações viraram abas (tabs) no inicio.html
- Antes: "Links" e "Publicações" eram duas colunas lado a lado com títulos empilhados (grid sm:grid-cols-2).
- Agora: barra de abas (Links | Publicações) lado a lado; clicar troca o painel exibido. Aba ativa = fundo branco + sombra + texto azul (#1e3a8a); inativa = cinza. Toggle via função inline `aocpShowTab()` + IDs aocpTabLinks/aocpTabPub. data-testid: tab-links-btn, tab-pub-btn, tab-links-panel, tab-pub-panel.
- Verificado por screenshot mobile: ambas as abas alternam corretamente. Lembrar Ctrl+Shift+R por causa do cache.

## Update 2026-06 (fork) — Abas Links/Publicações SÓ no mobile
- Correção: as abas devem aparecer apenas no mobile. No desktop voltaram as duas colunas lado a lado (original).
- Estrutura: grid original envolto em `<div class="hidden w-full lg:flex">` (grid com w-full) = escondido no mobile, visível no desktop; bloco de abas com `lg:hidden` = só no mobile.
- IMPORTANTE: neste build só existem as utilities responsivas `.lg:flex` e `.lg:hidden` (NÃO existe `.lg:block` nem `.lg:grid`). Usar sempre lg:flex/lg:hidden para alternar desktop/mobile.
- Verificado por screenshot: desktop 1280px mostra 2 colunas; mobile 390px mostra abas.

## Update 2026-06 (fork) — pagamento-pix: impressão sem duplicação + texto do botão
- Removida duplicação na impressão: o card do Edital (.aocp-edital-card) agora é escondido no @media print (adicionado à lista de hide). Na tela continua visível. Resultado: impressão sai só com o comprovante (print-header + dados), 1 página.
- Botão "Imprimir Pagamento" renomeado para "Imprimir Comprovante" (id p-btn-print, data-testid btn-imprimir-pagamento).
- Verificado: botão textContent = "Imprimir Comprovante"; edital card display=none em media=print.

## Update 2026-06 (fork) — Remover botão SAIR no mobile (todas as páginas do fluxo)
- O cabeçalho das páginas de fluxo é injetado por /aocp-header.v3.js dentro de um SHADOW DOM (host div#aocp-header-host). HTML e CSS ficam em base64 (HTML_B64/CSS_B64) decodificados por d().
- O botão SAIR é <a id="logout"><strong>SAIR</strong></a> dentro de .navbar-end no shadow root.
- Fix: acrescentado um <style> extra no innerHTML do shadow: @media(max-width:991px){#logout{display:none!important}}. Some no mobile em todas as páginas; no desktop continua.
- Verificado: getComputedStyle(#logout).display === 'none' em 360px; logo aparece inteiro.

## Update 2026-06 (fork) — Card do Edital menor no mobile (6 páginas)
- Bloco @media(max-width:640px) do .aocp-edital-card era idêntico em termos, inscricao, dados-inscricao, confirmacao, pagamento-pix, inscricao-realizada. Substituído por versão bem menor: aec-head padding 7px/10px + h3 12px; aec-body padding 10px + gap 8px + img 80px; aec-txt 11px. Só mobile; desktop inalterado.

## Update 2026-06 (fork) — Modal "Aviso importante" na página inicial
- Adicionado modal só no inicio.html (antes de </body>): logo Instituto AOCP (base64 do header), título azul #1e3a8a "Aviso importante", texto sobre encerramento das inscrições (08/09/2026 23h59min), botão pill azul "OK, entendi". Overlay rgba(15,23,42,.55).
- Abre automaticamente 1x por visita: sessionStorage key "aocp_aviso_saeb_v1". Fecha no botão ou clique no overlay. NÃO aparece nas demais páginas.
- data-testid: modal-aviso-overlay, modal-aviso-ok-btn. Verificado via DOM (abre flex, fecha none, flag=1, logoLen 33078).

## Update 2026-06 (fork) — Funil por dispositivo (Desktop x Mobile) no painel admin
- Backend: novo endpoint GET /api/admin/dashboard/funnel-devices (admin_routes.py, após o funnel). Retorna por etapa {label, desktop, mobile} para: Acessos ao site (accesses), Inscrições finalizadas (inscricoes finalized=True), PIX gerado/copiado/baixado. Device vem do doc; se faltar, infere do user_agent; para PIX usa mapa CPF->device da inscrição (funciona com dados antigos).
- Frontend: admin-extras.js injeta card "ORIGEM POR DISPOSITIVO" no dashboard (função injectFunnelDevices/findFunnelRow), inserido como card próprio logo após a linha Funil/Atividade. Cache bust index.html v=20260608c. data-testid n/a (build). Verificado: card alinhado (left 300, não sob a sidebar), dados batem com KPIs (15=13+2).

## Update 2026-06 (fork) — Fixes/seed
- Card "Origem por dispositivo" agora SÓ no Dashboard: ensureButton chama injectFunnelDevices sempre; quando não é dashboard, removeFunnelDevices() tira o card do DOM (antes ficava grudado ao trocar de rota). Cache bust index.html v=20260608d.
- track_registration agora grava device + user_agent na inscrição no momento da criação (antes só via patch do Telegram).
- Seed: /app/seed_inscricoes.py cria 300 inscrições realistas (nomes BR, CPF válido, cidades BA, IPs BR via X-Forwarded-For) espalhadas em ~10min, mix mobile/desktop, 3 cargos (Delegado 220 / Escrivão 190 / Investigador 190) e 4 comportamentos (gera / gera+copia / gera+baixa / gera+baixa+copia). Log em /app/seed.log. Roda contra localhost:8001.
