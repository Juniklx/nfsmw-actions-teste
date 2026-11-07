# NFSMW Android — PRE265: limites de tuning da BMW, auditoria do menu de desempenho (2026-11-07)

## Motivação
Após o ZIP PRE260, o usuário testou a BMW M3 GTR normal da carreira no Galaxy S24 FE e confirmou que pode dirigir, mas só vê Visual no menu. PRE262–264 mapearam `IsHeroCar` e o bloqueio de Peças/Desempenho ao `sub_82578988` PAL. O patch PRE264 foi somente ensaiado em memória, **guardado/desligado por padrão**, sem APK.

## PRE265 resultado verificável
- GitHub Actions, sucesso: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42321948518
- Backup PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, comprovado na auditoria.
- Examinados **131 arquivos** C++ de recompilação PAL. Fontes SHA256 fixados: `nfsmw_recomp.5.cpp` `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07` e `nfsmw_recomp.11.cpp` `0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3`.
- O bloco de menu `sub_82578988` tem **1 comparação BMW tipo 41**, 5 chamadas de adicionar categoria e continua consistente com ocultar Peças e Desempenho, mas mostrar Visual.
- O candidato de tela interna de desempenho `sub_82582F70` tem **2 comparações com tipo 41**; auditoria listou chamadas e encontrou o corpo de **8 funções auxiliares**, incluindo `sub_8256D2B8`, `sub_8256F818`, `sub_8256F9D8`, `sub_82579CE0`, `sub_8256D548`, `sub_8256BC60`, `sub_8256BB10`, `sub_82587498`.
- Referência de código público `dbalatoni13/nfsmw`: `CarCustomizeManager::GetNumPackages()` delega a `Physics::Upgrades::GetMaxLevel(ThePVehicle,type)`; `CustomizePerformance::Setup()` e `GetPerformancePartsList()` dependem desse resultado. Porém `PhysicsUpgrades.cpp` público não implementa `GetMaxLevel`. **Não foi possível comprovar nenhum valor de GetMaxLevel da BMW no aparelho nem nos dados de atributos.**
- Mock independente C++ com política `modelo BMW + carro de carreira validado + fora do prólogo + usuário ativou + contagem>0`: **5.904 cenários passaram**. Esse é apenas um controle sintético; **não** foi incorporado ao jogo ou ao código do menu. Um número zero em qualquer categoria faz a política recusar a abertura dessa categoria.
- **Conclusão:** a restrição visual da BMW tem origem plausível e identificável, mas abrir a categoria de Desempenho sem validar pacotes pode resultar em tela vazia/falha. **NÃO liberar PRE264 na APK sem cobertura desse caso**.

## Próximo passo
- PRE266 GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42322263103 — ensaio em árvore descartável PRE99 com instrumentação da V37 (sondas de dinheiro/nitro/speedbreaker) e alteração PRE264 de menu desligada por padrão, sem construir nem assinar APK. **Aguardando a conclusão para registrar evidências de integração.**
- Para habilitar V38 em produção, determinar em **runtime ou dados de atributos da edição** os pacotes realmente disponíveis à BMW e suportar `GetMaxLevel==0` sem acesso inválido. Proteger o prólogo e a classificação global HeroCar.
- V37 e save MARCEK intactos, sem alteração na chave permanente (cert SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`), package `io.github.nfsmwrecomp`; futura V38 precisa versionCode >=38 e a mesma chave, sem debug signing.

## Limitação do contexto
- O `CONTEXTO_NFSMW.md` no Drive permaneceu na PRE237 na última conferência. Esta nota é adendo preservado no GitHub, **não substituição** do histórico longo. Antes de sincronizar, fazer backup completo do arquivo e conciliar PRE238–266; nunca sobrescrever o contexto original com um resumo.
