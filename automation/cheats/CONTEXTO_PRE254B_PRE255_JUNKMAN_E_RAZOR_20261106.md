# NFSMW Android — PRE254B/PRE255 Junkman, economia e Razor (2026-11-06)

## Auditoria PRE254B concluída
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42314001961 — `completed/success`, `PRE254_STATUS AUDIT_OK`.
- Fonte original PRE99 autenticada: SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`.
- **795 arquivos** relevantes, **296.865.511 bytes** lidos. Nenhum arquivo/fonte alterado; nenhuma APK, chave, save ou instalação acessada.
- **0 resultados textuais diretos:** `Junkman`, `junk parts`, `unique performance`, `Razor`, `BMW M3`, `career reward`. O termo genérico `inventory` teve 20 coincidências em textos não relacionados à contagem de peças. `prologue` teve 15.556 ocorrências em grande parte devido à macro `REX_FUNC_PROLOGUE()` da recompilação, **não** evidência de história.
- Limite metodológico: o XEX recompilado tem funções nomeadas por endereços; zero correspondências textuais não provam que a funcionalidade não exista. O auditor não reverteu save, XEX original completo nem semântica dos tokens.
- Audit JSON preservado no Drive como ZIP: https://drive.google.com/file/d/1KUjEANu29AJSP93dVsYF8bbmDSzQH89f/view.
- Tentativa PRE254 inicial: run `42313833367` `failure` por `IndexError` no **auditor**, corrigido na PRE254B. Não foi falha de Android.

## Confirmação do débito do primeiro carro
- O mesmo auditor leu apenas contexto estático SHA-pinado da função PAL `sub_82564D80` — 5 stores de saldo encontrados na fonte original.
- No **5º store dessa função = site 8 da PRE246**, PC candidato `0x8256608C`, o código verifica `cmplw r3,r10` (compara valor a pagar com saldo), então, no ramo compatível, executa `subf r5,r3,r10` e grava `stw r5,12(r11)`. Isso confirma **saldo novo = saldo anterior − valor calculado pelo jogo**, condizente com a compra realmente observada em PRE253B (30.000 − 27.000 = 3.000). Não pressupor que seja a única rotina de crédito/debito.
- Não substituir store por NOP sem provas de persistência/semântica da compra.

## Referência externa Junkman (APENAS PC 1.3)
- Referência consultada: https://github.com/sprintstate/nfs-mw-save-editor e https://github.com/sprintstate/nfs-mw-save-editor/blob/main/docs/JUNKMAN_OFFSETS.md .
- PC 1.3 usa um conjunto de slots de **fichas de recompensa**. Quantidade de um tipo se obtém contando os slots com aquele Type_ID; editor permite quantidade desejada por tipo. O estudo para PC inclui categorias de performance freios/motor/nitro/turbo/suspensão/pneus/transmissão e também outras fichas.
- **Não copiar offsets `0x5769`, stride 12, quantidade total de 59 slots nem mapeamento numérico de Type_ID para Xbox360/PAL** sem validação específica. Mesmo que tamanhos de arquivo se pareçam, isso NÃO prova layout equivalente.

## PRE255 — política sintética de edição por tipo
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42314430558 — `completed/success`, `PRE255_STATUS AUDIT_OK`, `PRE255_SYNTHETIC_CASES 20000`.
- Código isolado: `automation/cheats/pre255_junkman_slot_policy.py` e `pre255_junkman_slot_policy_test.py`, somente repositório; **não foi integrado ao jogo, compilado para Android nem aplicado a save**.
- Entrada abstrata: slots previamente verificados, tipo validado, quantidade desejada, capacidade e limite aprovados pelo futuro adaptador de formato. Saída imutável; remove excesso de fichas apenas daquele tipo ou acrescenta em slots confirmadamente vazios; preserva fichas de outros tipos, inclusive desconhecidos; recusa tipos não autorizados, quantidade negativa/fora de limites e falta de espaço. Testes aleatórios verificaram contagens, invariantes e idempotência.
- **Sem prova do formato Xbox 360**, essa política é apenas componente preparatório, não feature usável na V37.

## Localização da área de saves observada
- Logs V37 anteriores mostraram XamContentCreate em `/data/user/0/io.github.nfsmwrecomp/files/nativo/usuario/.../454107D9/00000001/NAME`, com payload `NAME` de **62.688 bytes**. Caminho interno privado: não alegar que shell comum ou gerenciador de arquivos consegue abri-lo.
- Drive pesquisado por `Junkman`, `SAVE`, `perfil` sem encontrar arquivo binário de carreira do usuário para comparar; encontrados somente relatórios, backups e documentos. Não inventar save de teste.

## Próxima etapa segura
1. Investigar e validar **o formato real de fichas de inventário e seus metadados de integridade** na edição Xbox 360 rodando PAL. Preferir obtenção de **cópia exportada com consentimento** do save via app (SAF/compartilhamento) ou por mecanismo já existente e seguro, não leitura arbitrária de endereços guest.
2. Comparar duas cópias verificadas de save do mesmo usuário antes/depois de adquirir/usar **uma única** ficha Junkman, com backups, logs e hashes para localizar estrutura; evitar alterar o save ativo durante o jogo.
3. Somente após provar layout, permitir interface `Junkman` com quantidade por categoria e mecanismo reversível, validando checksums, carregamento e persistência.
4. Em paralelo, Razor/BMW é trilha separada: corrida do prólogo com sabotagem e perda do carro são eventos do roteiro. Diferenciar vencer na pista de preservar BMW sem quebrar progressão; sem código ou patch comprovado nesta fase.
5. Nenhuma V38 foi compilada ou assinada; nenhuma chave, V35–V37, save, input, shaders, FPS, física ou proteção térmica foi alterada. Se houver build futura, `versionCode>=38`, pacote `io.github.nfsmwrecomp`, certificado original SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
6. Atualizar `CONTEXTO_NFSMW.md` canônico do Drive com este adendo **após backup e verificação de versão**, sem sobrescrever registro histórico indevidamente.
