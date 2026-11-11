# PRE693 — controle real Samsung, C3 e watchdog (2026-11-11)

## Arquivos autenticados
- Galaxy S24 FE, V51, package io.github.nfsmwrecomp, resolution 1920x1080, cap 60 FPS, swapchain MAILBOX.
- Log do aparelho: 1.231.837 bytes, 4.251 linhas, SHA256 5a950a82265b4306d7de5034548f2134532e739db49d48c330dffda00255c335, sessão 11:48:53.864–11:55:13.845 (379.981 segundos).
- Identidade Vulkan: driverID SamsungProprietary, driverName Samsung Proprietary driver, driverInfo SPAL Driver version 25.3.3. Não há carregamento de driver personalizado registrado.
- Log bruto PRIVADO Drive: https://drive.google.com/file/d/17HR9pJBVn-lEvgDJy4BwAPWChRJA20YU/view
- Relatório privado Drive: https://drive.google.com/file/d/131FOa6HdhsSV2BQ0JRlMpeAxte1AslzZ/view
- ZIP privado (MD+JSON sem log bruto) Drive: https://drive.google.com/file/d/1dRsfm0e2kIg4DfxFMZ6kCmIQUR0Xswbs/view

## Resultado C3 — problema COMUM a Samsung e RADV
- 11:49:19.260: PRE635_C3_TWOREQUEST_TRACE e guard PRE194_C3 consecutivos, copia_duplicada=true, indice_fuera=false, referencia_distinta=false; fallback protetor ativado.
- Assinatura exatamente igual às duas ocorrências RADV de PRE692, após ignorar frames/épocas absolutos: indice=0, en_vuelo=1, offset_primera=0, offset_segunda=51872, mismos_comandos=true, subir=true, trabajo_huella=0, datos_bytes=43648.
- Em cada ocorrência, frame=textura_frame e epoca_ahora=epoca_primera. Frame Samsung 1347; RADV 2291 e 1766.
- O defeito C3 NÃO é exclusivo do RADV. Não se sabe se os bytes de textura são iguais ou qual produtor cria o segundo pedido. Não remover a proteção de ApagarEnlaces nem reaplicar patches às cegas.

## Watchdog
- Controle Samsung: 0 marcadores [vigilante] e 0 episódios em 6m20s de log.
- RADV PRE692 11:10:29: 7 episódios (6 retomadas após 31,11,28,24,11,23s e último sem retomada registrada).
- É comparação observacional, não causal: cenas, carga, temperatura, caches, duração e estado interno não são equivalentes. Ausência de watchdog não exclui microstutter.

## C2 interno e carga GPU
- 18 histogramas nominais de 20s: 20.541 intervalos entre Swaps; 15–18ms = 15.905 (77,43%); 18–25ms = 4.059 (19,76%); >=25ms = 217 (1,06%); máximo isolado = 152,0ms.
- Momentos de maior custo GPU real por Swap: 11:49:54 = 16,03ms (1.037 swaps/20s); 11:50:14 = 15,91ms (1.048); 11:53:34 = 15,60ms (1.077); 11:53:54 = 16,29ms (1.032).
- C2 Swaps são métricas INTERNAS, não timestamps SurfaceFlinger de apresentação. Cena específica não comprovada. Não atribuir queda de rendimento exclusivamente à GPU ou ao driver.

## Reprodutibilidade e próximo gate
- Auditoria local PRE692: 1 sessão, 1 trace/guard C3 pareado, 0 watchdog; extração estruturada JSON no ZIP privado.
- Analisador GitHub automation/kaggle/pre692_c3_watchdog_log_readonly.py agora reconhece driver Samsung com proteção contra indicadores de drivers conflitantes.
- Gate sintético GitHub Actions 43044364970 completed/success, job 130604268463: Samsung identification PASS, same C3 signature as RADV PASS, ambiguous driver rejected PASS. CI não recebeu log real privado.
- PRE694: teste A/B/A controlado Samsung–RADV–Samsung, mesmo cenário, 1920x1080, cap 60, efeitos íntegros, coletor PRE690 e log com driver comprovado. Separar stall watchdog do pacing SurfaceFlinger e do C3. Auditar código V51 antes de qualquer patch.
- V51, assinatura permanente, saves, qualidade gráfica, controles e proteções térmicas preservados; sem APK nova ou ganho comprovado.
- CONTEXTO_NFSMW.md canônico ainda pendente de append com backup; este checkpoint não é atualização do canônico.

STATUS PRE693: SAMSUNG_REAL_CONTROL_PASS; C3_DUPLICATE_BOTH_DRIVERS_VERIFIED; SAMSUNG_WATCHDOG_MESSAGES_ZERO; C2_SLOW_WINDOWS_PRESENT; DRIVER_CAUSALITY_UNPROVEN; NO_APK; NO_PROVEN_FPS_GAIN.
