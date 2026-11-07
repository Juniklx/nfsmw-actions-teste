# NFSMW Android — PRE267/PRE268: identificação da montagem do submenu Desempenho e limite de GetMaxLevel ainda não demonstrado (2026-11-07)

## Referência verificada e objetivo
- Último APK funcional em telefone: **V37**, diagnóstico. Com ZIP PRE260, usuário confirmou BMW M3 GTR normal na garagem MARCEK e dirigível, mas apenas **Visual** disponível no tuning; Punto, saldo e Junkman preservados no arquivo exportado.
- PRE262–PRE266 localizaram bloqueio `HeroCar` do menu (função `sub_82578988` PAL) e testaram fonte guardada/desligada em árvore temporária, **sem build V38**.
- Código fonte público `dbalatoni13/nfsmw` examinado nesta etapa:
  - `CarCustomize.cpp`, `CustomizeSub::SetupPerformance()`: monta categorias **motor, transmissão, suspensão, nitro, pneus, freios, indução forçada** tanto em oficina normal quanto na backroom. Não há verificação de `GetMaxLevel` durante essa montagem.
  - `CarCustomizeManager::GetPerformancePartsList(type)`: itera até `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`. Uma contagem zero produz lista vazia.
  - `CustomizePerformance::RefreshHeader()`: utiliza `GetSelectedPart()->GetPhysicsType()` diretamente. Falta demonstrar que há lista não vazia para BMW, portanto abrir todas as telas cegamente apresenta risco teórico de acesso inválido (crash ainda **não observado**).
- Não equiparar templates/saves da variante normal BMW com `M3GTRCAREERSTART`, nem promover mocks isolados a compatibilidade Android comprovada.

## PRE267 — busca ampla PAL, somente leitura
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42322927425 — **success**, `PRE267_STATUS AUDIT_OK`.
- Backup PRE99 validado: SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- Os `nfsmw_recomp.*.cpp` PAL foram pesquisados por chamadas do helper de opções de menu `__imp__sub_82575370(ctx, base)`. Distribuição de contagens nas funções encontradas: `{9:1,11:1,8:1,13:1,5:1,10:2,6:1}`; nenhuma função com exatamente 14 chamadas. A multiplicidade **sozinha** não identifica um método.
- Principal candidata: **`sub_825767F0` PAL**, no `workspace/nativo/app/generated/default/nfsmw_recomp.39.cpp`, SHA256 `ac9c0f8f5d69a59c390010227263ece19ae4688ef4bc4d30d16ed622879bd0e4`. Contém 13 instruções de chamada estáticas e variáveis/ramificações em torno da última categoria.
- Drive (ZIP JSON técnico, sem save pessoal): https://drive.google.com/file/d/1dz9zYP2wvA-lh0lhKqqTIngcI1wJioly/view

## PRE268 — janela de instruções SHA-pinned e fluxo de chamadas
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42323202221 — **success**, `PRE268_STATUS AUDIT_OK`.
- SHA-pinned `nfsmw_recomp.39.cpp`, `.34.cpp`, `.90.cpp` e `.57.cpp`, fontes PRE99 autenticadas; nenhuma fonte nem save modificados.
- `sub_825767F0`: lista as categorias com instruções `li r7,513`, `514`, `515`, `516`, `517`, `518` nas duas seções de oficina, e há ramificação para indução forçada. São sequências **fortemente consistentes** com `CustomizeSub::SetupPerformance()` do código público. A última categoria compartilha blocos de ramificação, explicando por que uma contagem literal de chamadas não equivale diretamente à descrição de alto nível.
- O helper **`sub_8256F9D8` é chamado duas vezes**, uma em cada seção da rotina; os parâmetros e o uso subsequente do resultado booleano são consistentes com uma consulta do tipo `IsTurbo`, **não provam GetMaxLevel**.
- Outros alvos inspecionados: `sub_8256D2B8` (`nfsmw_recomp.34.cpp`), `sub_8256F9D8` (`.90.cpp`) e `sub_8256F818` (`.57.cpp`), sem atribuição definitiva de `GetPerformancePartsList` ou `GetMaxLevel`. Nunca marcar candidatos como símbolos comprovados.
- **Resultado crítico:** `PRE268_BMW_GETMAXLEVEL_KNOWN False`; a auditoria mapeou o caminho do **submenu**, mas não recuperou os valores efetivos de 7 categorias da BMW. Não afirmar que upgrades são impossíveis, nem que funcionam.
- Drive (ZIP JSON técnico): https://drive.google.com/file/d/1G34n1UnvnXjYqPMMWm3ybD_sFO3F3tt0/view

## Estado e próxima decisão
- BMW M3 GTR normal: **dirigível confirmado por usuário**.
- Tuning BMW: **só Visual confirmado por usuário**.
- `HeroCar` bloqueia Peças/Desempenho: **identificado na fonte pública; função de menu PAL fortemente correlacionada**.
- Submenu Desempenho PAL `sub_825767F0`: **mapeamento estático de forte consistência**, mas não runtime.
- **`GetMaxLevel()` da BMW:** contagens não medidas. Precisa ser identificado/testado antes de habilitar a PRE264; planejar instrumentação **passiva segura** com valores efetivos sem alocar opções nulas, ou analizar dados de atributos da edição em que a BMW é executada.
- No futuro, habilitar menu apenas para BMW de carreira sob opt-in, nunca alterar globalmente IsHeroCar ou proteção do prólogo. Verificar 7 pacotes/zero count, comportamento de backroom Junkman, renderização, compra, persistência e rollback. Caso V38, versionCode >=38, mesma assinatura permanente, nunca recriar chave ou usar debug.
- As PRE267/PRE268 **não geraram APK, não assinaram release, não instalaram nada**, não tocaram no save MARCEK, não alteraram árvores originais, nem demonstraram ganho de FPS. V37 e assets/PG-9076/shaders/física/1920x1080/proteções térmicas preservados.
- **Contexto canônico Drive `CONTEXTO_NFSMW.md`** ainda na PRE237 em última leitura; esta nota deve ser incorporada **após backup, conferindo atualizações posteriores**, sem substituir o histórico com síntese incompleta.
