# NFSMW Android — PRE276: funções auxiliares de atributos e segundo nível de efeitos colaterais (2026-11-07)

## Base e objetivo
- Estado validado em aparelho: usuário consegue selecionar e dirigir **BMW M3 GTR normal** inserida via save PRE260 no perfil **MARCEK** da V37. Na oficina, apenas **Visual** aparece; classificação `HeroCar` oculta `Peças` e `Desempenho`. Fiat Punto, Junkman, outros perfis e APK V37 preservados.
- PRE269–275 rastrearam estruturalmente a consulta de limites `sub_823E5988` PAL (candidata a `Physics::Upgrades::GetMaxLevel`), que retorna quantidades via atributos do carro, e comprovaram **escritas de memória guest fora da pilha** em `r11+18`. Não é função pura; **não aprovar sete chamadas artificiais na inicialização de tuning**.
- Objetivo PRE276: inspecionar os quatro auxiliares diretamente chamados pelas duas funções de atributos da PRE275, distinguindo escrita direta de efeitos indiretos.

## PRE276 — evidência
- GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42326530780 — execução **success**, log `PRE276_STATUS AUDIT_OK`, `PRE276_EXTRA_LEVEL_CALLS_APPROVED False`.
- Código reproduzível: `automation/kaggle/pre276_bmw_getmaxlevel_callee_transitive_readonly.py`, workflow `.github/workflows/nfsmw-pre276-bmw-attribute-callee-readonly.yml`.
- Fonte **PRE99 autenticada**, SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, C++ gerado PAL, nenhuma fonte modificada. Arquivo JSON sanitizado arquivado no Drive: https://drive.google.com/file/d/1mUJ1AM95RxBWu32l4zDGVrnRYvZu1Atw/view
- Função `sub_82148718` (PAL `nfsmw_recomp.8.cpp`, 147 linhas): **13 stores guest**; 8 com endereços fora da pilha ou ainda sem classificação, 5 diretamente em frame da pilha. Há stores de 32 bits em `r29+{0,4,8,12}` e U16 em `r11+18`, `r8+18`, `r11+18`; chama `sub_821485E8` e `sub_8214E928`.
- `sub_8214E9E0` (PAL `nfsmw_recomp.9.cpp`, 51 linhas): **6 stores guest**, todos fora da pilha ou sem classificação: quatro gravações U32 nos campos de um registro `r3+{0,4,8,12}` e duas U16 em `r11+18`. Não tem callee direto do tipo `sub_...`.
- `sub_82145428` (PAL `nfsmw_recomp.44.cpp`, 74 linhas): **0 stores guest e 0 chamadas diretas** no corpo gerado inspecionado.
- `sub_82145C50` (PAL `nfsmw_recomp.98.cpp`, 58 linhas): **0 stores guest e 0 chamadas diretas** no corpo gerado inspecionado.
- As duas funções sem stores diretas podem ser candidatas a consultas puras **nesse nível**, mas não se declarou pureza geral: requer atenção a outras formas de estado/caminhos externos.
- Em conjunto, os padrões `r11+18` e cópia de campos de 16 bytes são **consistentes com estruturas administradas por referências**, porém o pareamento de increments/decrements em todos os ramos, identidade dos objetos e efeitos em cache **não foram comprovados**.
- **Níveis reais de upgrades da BMW: não foram medidos.** Auditoria é estática; sucesso do workflow não representa testes físicos nem compatibilidade de upgrades.

## Decisão e próximo passo
1. **Não inserir** sete chamadas adicionais a `GetMaxLevel()` ao entrar no tuning e **não** ativar indiscriminadamente o patch `HeroCar` PRE264. Nada foi aplicado à V37.
2. Priorizar captura dos valores de **chamadas naturais** por instrumentação passiva PRE271/PRE274, com marcador de entrada que permita correlacionar o carro; reconhecer que a BMW pode não executar GetMaxLevel em personalização enquanto o menu fica bloqueado.
3. Para aprender os limites sem chamadas guest adicionais, estudar formato dos dados de atributos e obter uma leitura **realmente sem escrita e válida** dos sete níveis; em paralelo, localizar o controle de `GetSelectedPart()==nullptr` antes de expor menus vazios.
4. Se auditar ciclo de vida, próximos subcaminhos `sub_821485E8` e `sub_8214E928` devem ser analisados e pareados com escritos `+18`; nenhuma prova atual de que chamadas extras são seguras.
5. Futuras builds somente após revisão e backup, package `io.github.nfsmwrecomp`, incremento de versionCode além de V37 (pelo menos 38), **mesma chave/certificado permanente** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nunca recriar chave, não usar debug, nunca solicitar/expor senha. Preservar V37, saves, PG-9076, 1920×1080, gráficos, efeitos, física e limites térmicos.
6. Contexto canônico `CONTEXTO_NFSMW.md` no Drive foi verificado nesta sessão e ainda termina em PRE237. Esta nota aditiva fica no GitHub sem sobrescrever o histórico extenso. Para consolidar no Drive, exigir **backup completo e conciliação** de PRE238–276.

## Status
- PRE276 scanner: validado GitHub Actions, só leitura.
- Helper com estado lateral: confirmado.
- Leitura de upgrades da BMW: não validada no aparelho.
- APK V38: não compilada, não assinada e não instalada. V37 e MARCEK preservados.
