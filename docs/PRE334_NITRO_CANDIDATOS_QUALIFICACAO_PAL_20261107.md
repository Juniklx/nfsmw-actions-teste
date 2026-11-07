# PRE334 — Qualificação PAL dos seis candidatos estruturais Nitro (2026-11-07)

## Execução e evidências verificadas
- GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42411632872, job `128520826364`: `completed/success`.
- Snapshot PRE99 autenticado; 129 shards PAL; status `PRE334_STATUS AUDIT_OK`, `PRE334_FUNCTIONS 6`, `PRE334_NITRO_SHAPED 1`, `PRE334_OWNER_VERIFIED False`.
- Artifact `13589207868` lido integralmente; resumo `docs/generated/PRE328_PRE334_SANITIZED_STATUS.json` conferido.
- Código `automation/kaggle/pre334_pal_nitro_layout_qualification_readonly.py`; mock sintético `automation/kaggle/pre334_pal_nitro_layout_qualification_mock.py`; workflow `.github/workflows/nfsmw-pre334-pal-nitro-qualification.yml`.
- A classificação exige simultaneamente: atribuição do registrador-base a `ctx.r3` nos primeiros 90 trechos da função, leitura em `+252`, gravação em `+252` e leitura em `+296` (todos no mesmo registrador-base). É uma análise textual do PAL original, **não uma prova de classe ou owner**.

| Função | Base | Entrada direta de r3 | LOAD +252 | STORE +252 | LOAD +296 | Assinatura completa |
|---|---|---|---:|---:|---:|---|
| `sub_822040B0` | `ctx.r11` | Não | 0 | 1 | 0 | Não |
| `sub_82424AF0` | `r31` | Sim | 4 | 5 | 3 | **Sim** |
| `sub_825904F0` | `r31` | Não | 0 | 0 | 0 | Não |
| `sub_8270BF50` | `r31` | Sim | 0 | 1 | 0 | Não |
| `sub_82719CB0` | `r31` | Sim | 0 | 1 | 0 | Não |
| `sub_828A61D8` | `r31` | Não | 0 | 1 | 0 | Não |

- Contagens de LOAD/STORE são **ocorrências estáticas do código**, não o número de eventos runtime.
- Os cinco candidatos rejeitados ainda podem ser funções válidas do jogo, mas **não são equivalentes à rotina Nitro segundo este critério**.
- PRE333 tinha 315 assinaturas de campos; PRE334 qualificou apenas os **seis candidatos com todos os cinco deslocamentos**, não os 315. Não afirmar que os outros 309 foram descartados por esta prova mais estrita.

## Conclusão
A evidência reforça a identidade funcional de `sub_82424AF0` como rotina do medidor Nitro (PRE321, PRE323, PRE329, PRE330), sem provar que `ctx.r3` pertence ao jogador. O deslocamento `r31+252` segue observado; a base guest `0xBFA9E700` foi calculada somente na sessão V41 verificada e não deve ser fixada em patch.

## Próximo gate técnico
1. Obter referência independente e autenticada ao objeto do veículo controlado pelo jogador ou método de desambiguação contextual verificável.
2. Preparar correlação runtime limitada, passiva, com estado `jogador/outro/indeterminado` e **indeterminado por padrão**. Sem leituras arbitrárias guest e sem reescrever stores.
3. Somente após teste físico A/B em Galaxy S24 FE comparar owner e avaliar opção Nitro opt-in fail-closed OFF=original, sem reduzir gráficos, controles, térmica ou alterar save.

## Integridade
Nenhum patch do jogo, APK V42, chave, assinatura, save `MARCEK` ou configuração foi alterado. V41 segue a referência de instrumentação Nitro. Nenhum ganho de FPS alegado.
