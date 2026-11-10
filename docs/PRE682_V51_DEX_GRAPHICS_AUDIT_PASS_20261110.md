# PRE682 — auditoria do DEX real da APK V51 aprovada

Data: 2026-11-10.

## Execução e evidências verificadas

- **Repositório**: `Juniklx/nfsmw-actions-teste` público.
- **Workflow**: `.github/workflows/nfsmw-pre682-v51-dex-graphics-readonly.yml`.
- **Commit de disparo**: `1981ec118715418c73f6fbcb3eb8f2ba4413597b`.
- **Run Actions**: `42910788328`, job `130160579462`, status `completed`, conclusão `success`.
- **ZIP privado do Drive**: `NFSMW_Android/06_Logs_e_Medicoes/NFSMW_PRE682_V51_DEX_GRAPHICS_20261110_220330.zip`, ID `1pkpOUw0jDBDDwzSZH9VZ2tM6b-uGR3zD`, 1447 bytes, SHA256 `6603d180d69cf4e1c9389f83d180f5dc07074307b26a469d501abfaa8629bfe2`, ZIP CRC PASS.
- **APK base**: V51 PRE652, 47.104.417 bytes SHA256 `207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b`. Nenhuma alteração.
- **DEX autêntico**: SHA256 `be3c0393307d5e0128eab4f0f590e44fc480581c4eedfc537c58fc58414cb689`.
- **Prova estática**: classe `MotorNativo`, método `argumentos()`, contém literais de resolução, FPS, desfoque, PCF, sombra de vegetação, resolução/distância da sombra, reflexos do carro/asfalto e brilho do céu, e referências de chamadas a `Ajustes.desenfoque`, `calidadSombras`, `sombrasEscala`, `sombrasCorte`, `resolucionInterna` e `limiteFps`. Classe `Ajustes` inclui getters com chaves de `SharedPreferences` e `getBoolean`, `getString`, `getInt` correspondentes.

## Captura da tela do próprio app

O usuário enviou screenshot antes de iniciar o jogo: Vulkan, 1920x1080, 60fps, sombras Xbox 360 / Ultra / Longe, anisotrópico 16x, reflexos Altos, reflexo de asfalto molhado ativado, desfoque de velocidade ligado, filtro de cor pela metade, suavização desativada, escalonamento bilinear, filtro de imagem nenhum.

**Limite**: screenshot mostra escolhas na UI; não é leitura direta de `SharedPreferences` nem confirma argumentos e cvars do motor em execução. O scanner DEX confere co-ocorrência de referências dentro do mesmo método; não rastreia controle de fluxo nem registradores e não prova a negação booleana aplicada em todas as rotas.

## Interpretação e próximo passo

- Defaults do TOML empacotado identificados na PRE681 não podem ser tratados como as opções ativas do dispositivo.
- Não otimizar GPU/shaders reduzindo efeitos com base nesses defaults.
- Próximo gate PRE683: observar argumentos/cvars em execução com coleta limitada e autorizada, ou instrumentação de diagnóstico reversível e assinada pela chave permanente após gates. Priorizar preservar qualidade e segurança.
- V51 é a release atual; `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nenhuma V52 criada nem melhoria FPS demonstrada.
- Atualização canônica do Drive: workflow PRE682_CONTEXT foi **disparado** pelo commit `a10a6d96f7f9f272468f400facd6f5a58ca2e025`, mas sua conclusão/readback ainda não foram confirmados. Este adendo GitHub não substitui o `CONTEXTO_NFSMW.md` do Drive.

Status: PRE682_SIGNED_V51_DEX_STATIC_AUDIT_PASS; UI_OPTIONS_OBSERVED; ACTIVE_CVARS_UNKNOWN; NO_APK; NO_FPS_GAIN.
