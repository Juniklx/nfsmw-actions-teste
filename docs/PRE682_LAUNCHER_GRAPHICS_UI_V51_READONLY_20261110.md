# PRE682 — tela de configurações gráficas e auditoria do caminho Java (2026-11-10)

## Evidência do usuário

O usuário enviou uma captura das preferências exibidas **antes de iniciar o jogo** no aplicativo NFSMW e esclareceu expressamente que é a interface do próprio app, **não GitHub Actions**. Não publicar a imagem original nem supor que a captura concede acesso a `SharedPreferences`.

Valores visíveis da captura:
- API Vulkan.
- Resolução interna 1920x1080; limite 60 FPS.
- Suavização de bordas desligada; bilinear; anisotrópico 16x.
- Sombras "Como no Xbox 360"; resolução de sombras "Ultra"; distância "Longe (como o jogo)".
- Reflexos do carro "Altos"; reflexo de asfalto molhado ligado.
- Brilho do céu "Natural"; filtro de cor "Pela metade".
- Desfoque de velocidade ligado; filtro de imagem "Nenhum".

São **escolhas apresentadas na UI**. Não foram lidos os valores salvos no dispositivo, os argumentos efetivamente recebidos pelo motor na sessão nem os valores finais de cvars. Tampouco há prova de fidelidade visual de todos os shaders apenas pelo menu.

## Auditoria real do snapshot-fonte histórico do Drive

Arquivo consultado: `01_Jogos_e_Fonte/NFSMW-Recompiled-Mobile-main.zip` (Drive ID `11jLQdQ7UshqWfQ0xctZhVZdCjGbUWHL_`; snapshot anterior à instrumentação da V51 — **não afirmar que é bytecode idêntico ao DEX assinado**).

- `android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java`:
  - linha 501: `desenfoque()` obtém preferência `desenfoque`, default falso.
  - linhas 518-523: qualidade das sombras `rapida`, `suave`, `xbox360`.
  - linhas 531-536: `sombrasEscala()` / `sombrasCorte()`; `100` do corte corresponde à distância original do jogo.
  - linhas 493-494 e 485-486: leitura de resolução interna e cap de FPS do menu.
- `android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java`:
  - linhas 237-239: argumentos de resolução e limite FPS.
  - linha 245: `--nfsmw_nativo_sin_desenfoque=` recebe o inverso de `ajustes.desenfoque()`.
  - linha 248: `--nfsmw_nativo_pcf_barato=` recebe comparação com `SOMBRAS_RAPIDA`.
  - linha 249: `--nfsmw_sombras_sin_vegetacion=` recebe negação de `SOMBRAS_XBOX`.
  - linhas 250, 254-257: argumentos de resolução/alcance das sombras, reflexos e brilho do céu.
  - linha 242: `nfsmw_antialiasing` mapeia FXAA ou desligado; o comentário diz que MSAA não é suportado no caminho de cena em uma passagem.

**Inferência condicional:** se a captura reflete as preferências realmente lidas por `Ajustes`, e se o fluxo arquivado corresponde ao DEX que roda no S24 FE, o launcher deve emitir `--nfsmw_nativo_sin_desenfoque=false`, `--nfsmw_nativo_pcf_barato=false` e `--nfsmw_sombras_sin_vegetacion=false`. Não promover essa inferência a parâmetros ativos confirmados; a PRE680 não os registrou no `nfsmw.log`.

## Comparação com PRE681

A auditoria PRE681 real via Actions run `42902067651` aprovou CRC/hashes da V51 e identificou defaults no TOML empacotado `nfsmw_nativo_sin_desenfoque=true`, `nfsmw_nativo_pcf_barato=true` e `nfsmw_sombras_sin_vegetacion=true`. Esses defaults diferem do que o código histórico deve construir a partir do menu mostrado. O log PRE656 confirmou apenas 1920x1080 e cap 60 naquela execução, não os efeitos.

## Próximo gate seguro

- Confirmar no DEX real da V51 ou em uma **instrumentação diagnóstica explicitamente controlada** que os valores do menu entram nos argumentos finais e nas cvars do motor. Sem alterar qualidade, renderer, shaders, opção do usuário ou assinatura.
- Para investigar percepção de fluidez a 60 FPS, obter frametimes/intervalos de apresentação na mesma sessão antes de atribuir a shaders/CPU ou qualidade; 60 FPS como limite não prova regularidade de quadros.
- Atualizar também `NFSMW_Android/CONTEXTO_NFSMW.md` no Drive canônico com esta evidência quando houver backup e readback verificados.
- V51 PRE652 preservada, certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nenhum patch, APK nova ou ganho de FPS nesta etapa.

STATUS: PRE682_UI_SCREENSHOT_OBSERVED; HISTORICAL_JAVA_MAPPING_CONFIRMED; V51_LIVE_CVARS_NOT_VERIFIED; NO_APK_CHANGE.
