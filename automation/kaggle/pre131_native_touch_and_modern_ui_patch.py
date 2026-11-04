#!/usr/bin/env python3
"""PRE131: Android touch drag state machine + actual UI typography/label redesign.

Use exact PRE128 settings hash, PRE99 unchanged ImGuiDrawer and headers. The
existing bundled Android Michroma TTF is embedded only in the ephemeral build.
No persistent source backup, runtime controls, graphics, saves, or keys touched.
"""
from __future__ import annotations
import hashlib
import re
from pathlib import Path

PRE128_CPP_SHA="cf3cc930904303ec3b4a081f9987a1ced478697678fcab90b056f07ba0b4957d"
PRE99_DRAWER_CPP_SHA="1a62d13e81af3aac4837af06e90281b64bd282c78e6e5ce079d6ca930e8a5c24"
PRE99_DRAWER_HEADER_SHA="931534a68dbeb10d85b3a100152e390170289ddf283c75d9c3246f4d3a96ecb7"
PRE99_SETTINGS_HEADER_SHA="495654dd11c214bf1f8aa4bc252be3984c85746f2cfec313f62ea586418dcc50"
FONT_SHA="b62301163788bc5b7f8fcac0b74b184e34e1827e577b499ecb724da065098f87"

def h(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def exact(source:str,old:str,new:str,label:str)->str:
    count=source.count(old)
    if count!=1:raise ValueError("PRE131 anchor missing/duplicate "+label+" count="+str(count))
    return source.replace(old,new,1)

def generate_font_header(font:bytes)->bytes:
    if len(font)!=64344 or h(font)!=FONT_SHA:raise ValueError("Bundled Michroma TTF was altered")
    rows=[]
    for i in range(0,len(font),20):
        rows.append("  "+", ".join("0x%02x"%b for b in font[i:i+20])+",")
    return ("#pragma once\n// Generated only in isolated runner from Android's existing michroma.ttf.\n"
            "// This is not exported as a font artifact or standalone font file.\n"
            "static const unsigned char kNfsmwModernFontData[] = {\n"
            +"\n".join(rows)+"\n};\n").encode("utf-8")

def proposal(settings_cpp:bytes,drawer_cpp:bytes,drawer_h:bytes,settings_h:bytes,font:bytes)->dict[str,bytes]:
    expected=(("settings",settings_cpp,PRE128_CPP_SHA),("drawer cpp",drawer_cpp,PRE99_DRAWER_CPP_SHA),
              ("drawer header",drawer_h,PRE99_DRAWER_HEADER_SHA),
              ("settings header",settings_h,PRE99_SETTINGS_HEADER_SHA))
    for label,blob,hash_expected in expected:
        if h(blob)!=hash_expected:raise ValueError("PRE131 unexpected source "+label)
    generated=generate_font_header(font)
    settings=settings_cpp.decode("utf-8")
    drawer=drawer_cpp.decode("utf-8")
    dh=drawer_h.decode("utf-8")
    sh=settings_h.decode("utf-8")

    dh=exact(dh,"  ImGuiIO& GetIO();\n",
             "  ImGuiIO& GetIO();\n"
             "  // PRE131: input source is tracked by OnTouchEvent, not SDL mouse emulation.\n"
             "  bool IsTouchPointerActive() const {\n"
             "    return touch_pointer_id_ != TouchEvent::kPointerIDNone;\n"
             "  }\n","touch source query")

    drawer=exact(drawer,"namespace rex {\nnamespace ui {",
        "#if defined(__ANDROID__)\n#include \"nfsmw_modern_font.h\"\n#endif\n\n"
        "namespace rex {\nnamespace ui {","font include")
    drawer=exact(drawer,
        """  io.Fonts->AddFontFromMemoryCompressedBase85TTF(kProggyTinyCompressedDataBase85, 10.0f,
                                                 &font_config, font_glyph_ranges);""",
        """  io.Fonts->AddFontFromMemoryCompressedBase85TTF(kProggyTinyCompressedDataBase85, 10.0f,
                                                 &font_config, font_glyph_ranges);
#if defined(__ANDROID__)
  // PRE131: dedicated readable modern font for Android Settings.
  // Keep ProggyTiny as the default for desktop and other overlays.
  ImFontConfig modern_font_config;
  modern_font_config.FontDataOwnedByAtlas = false;
  modern_font_config.OversampleH = modern_font_config.OversampleV = 2;
  modern_font_config.PixelSnapH = false;
  io.Fonts->AddFontFromMemoryTTF(
      const_cast<unsigned char*>(kNfsmwModernFontData),
      sizeof(kNfsmwModernFontData), 16.0f,
      &modern_font_config, font_glyph_ranges);
#endif""","modern font initialization")

    sh=exact(sh,"  std::string capturing_bind_name_;\n",
        """  std::string capturing_bind_name_;
  // PRE131: per-dialog finger drag tracking (no desktop side effects).
  bool touch_scroll_tracking_ = false;
  bool touch_scroll_excluded_ = false;
  float touch_scroll_start_y_ = 0.0f;
  float touch_scroll_last_y_ = 0.0f;
""","touch state")

    helper="""// PRE131: display names only. Keep raw CVar registry keys and save format.
static std::string MobileFriendlySettingName(const std::string& raw) {
  std::string out = raw;
  bool beginning = true;
  for (char& ch : out) {
    if (ch == '_') {
      ch = ' ';
      beginning = true;
    } else if (beginning && ch >= 'a' && ch <= 'z') {
      ch = char(ch - 'a' + 'A');
      beginning = false;
    } else if (ch != ' ') {
      beginning = false;
    }
  }
  return out;
}

"""
    settings=exact(settings,"void SettingsDialog::OnDraw(ImGuiIO& io) {",
             helper+"void SettingsDialog::OnDraw(ImGuiIO& io) {","friendly labels helper")
    settings=exact(settings,"  const bool settings_visible = ImGui::Begin(",
        """  // PRE131: use the app's bundled modern font for Android Settings only.
  const bool modern_font = mobile_layout && ImGui::GetIO().Fonts->Fonts.Size > 1;
  if (modern_font) {
    ImGui::PushFont(ImGui::GetIO().Fonts->Fonts[1]);
  }
  const bool settings_visible = ImGui::Begin(""","font start")
    settings=exact(settings,
        """  if (!settings_visible) {
    ImGui::End();
    return;
  }""",
        """  if (!settings_visible) {
    ImGui::End();
    if (modern_font) ImGui::PopFont();
    return;
  }""","font early return")
    settings=exact(settings,
        'ImGui::InputText("##search", search_buf_, sizeof(search_buf_));',
        'ImGui::InputTextWithHint("##search", "Pesquisar configuracoes...", search_buf_, sizeof(search_buf_));',
        "search placeholder")
    if settings.count('"All settings"')<1:
        raise ValueError("PRE131 missing default category text")
    settings=settings.replace('"All settings"','"Todas as configuracoes"')
    if settings.count('"CATEGORY"')==1:settings=settings.replace('"CATEGORY"','"CATEGORIA"')
    settings=settings.replace('"SETTINGS  /  ANDROID"','"AJUSTES  /  ANDROID"')

    label_rx=r'''      ImGui::TextColored\(
          LifecycleColor\(
              entry\.lifecycle,
              imgui_drawer\(\)->style\(\)\.settings\),
          "%s",
          entry\.name\.c_str\(\)\);'''
    label_new="""      const std::string visible_name =
          mobile_layout ? MobileFriendlySettingName(entry.name) : entry.name;
      ImGui::TextColored(
          mobile_layout ? ImVec4(0.94f, 0.94f, 0.91f, 1.0f)
                        : LifecycleColor(entry.lifecycle,
                                         imgui_drawer()->style().settings),
          "%s",
          visible_name.c_str());"""
    settings,count=re.subn(label_rx,lambda m:label_new,settings)
    if count!=1:raise ValueError("PRE131 label regex expected 1, got "+str(count))

    scroll_old="""  // PRE128: an Android finger is reported by SDL as a primary mouse drag.
  // ImGui's scrollbar handles itself, but a drag over passive labels/blank
  // space does not generate a wheel event. Scroll the single ROOT window.
  // Never steal touches from active text inputs, sliders, selectors or buttons.
  if (mobile_layout && !ImGui::IsAnyItemActive() &&
      ImGui::IsWindowHovered(ImGuiHoveredFlags_RootAndChildWindows) &&
      ImGui::IsMouseDragging(ImGuiMouseButton_Left, 12.0f) &&
      io.MouseDelta.y != 0.0f && ImGui::GetScrollMaxY() > 0.0f) {
    ImGui::SetScrollY(ImGui::GetScrollY() - io.MouseDelta.y);
  }

  ImGui::PopStyleColor(mobile_layout ? 25 : 11);
  ImGui::PopStyleVar(4);
  ImGui::End();"""
    scroll_new="""  // PRE131: the native ImGuiDrawer::OnTouchEvent stores the finger in
  // io.MousePos/io.MouseDown, but ImGui::IsMouseDragging and hovered-window
  // checks from PRE128 did not scroll on the S24 FE (observed on V28).
  // Track that real native touch pointer explicitly and scroll the ROOT only.
  // A touch beginning on an interactive control still belongs to that control.
  if (mobile_layout) {
    const bool finger_down =
        imgui_drawer()->IsTouchPointerActive() && io.MouseDown[0];
    const ImVec2 window_pos = ImGui::GetWindowPos();
    const ImVec2 window_size = ImGui::GetWindowSize();
    const bool within_settings =
        io.MousePos.x >= window_pos.x &&
        io.MousePos.x < window_pos.x + window_size.x &&
        io.MousePos.y >= window_pos.y &&
        io.MousePos.y < window_pos.y + window_size.y;
    if (!finger_down) {
      touch_scroll_tracking_ = false;
      touch_scroll_excluded_ = false;
    } else if (!touch_scroll_tracking_) {
      touch_scroll_tracking_ = within_settings;
      touch_scroll_excluded_ = ImGui::IsAnyItemActive();
      touch_scroll_start_y_ = io.MousePos.y;
      touch_scroll_last_y_ = io.MousePos.y;
    } else {
      const float delta_y = io.MousePos.y - touch_scroll_last_y_;
      if (within_settings && !touch_scroll_excluded_ &&
          std::fabs(io.MousePos.y - touch_scroll_start_y_) > 12.0f &&
          delta_y != 0.0f && ImGui::GetScrollMaxY() > 0.0f) {
        const float requested = ImGui::GetScrollY() - delta_y;
        const float clamped =
            std::max(0.0f, std::min(requested, ImGui::GetScrollMaxY()));
        ImGui::SetScrollY(clamped);
      }
      touch_scroll_last_y_ = io.MousePos.y;
    }
  }

  ImGui::PopStyleColor(mobile_layout ? 25 : 11);
  ImGui::PopStyleVar(4);
  ImGui::End();
  if (modern_font) ImGui::PopFont();"""
    settings=exact(settings,scroll_old,scroll_new,"new native swipe state machine")
    settings=exact(settings,
        "#include <algorithm>\n",
        "#include <algorithm>\n#include <cmath>\n",
        "floating-point gesture threshold")
    if settings.count("PRE117: Android uses the root Settings window as the sole scroll owner.")!=1:
        raise ValueError("PRE131 lost PRE117 single-scroll patch")
    if settings.count('ImGui::BeginChild("##cvars"')!=1:
        raise ValueError("PRE131 changed unique CVar child declaration")
    return {
        "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp":settings.encode("utf-8"),
        "workspace/nativo/sdk/include/rex/ui/overlay/settings_overlay.h":sh.encode("utf-8"),
        "workspace/nativo/sdk/src/ui/imgui_drawer.cpp":drawer.encode("utf-8"),
        "workspace/nativo/sdk/include/rex/ui/imgui_drawer.h":dh.encode("utf-8"),
        "workspace/nativo/sdk/src/ui/nfsmw_modern_font.h":generated
    }
