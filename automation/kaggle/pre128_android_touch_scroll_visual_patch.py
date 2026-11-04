#!/usr/bin/env python3
"""PRE128 proposal: native Android swipe-to-scroll + finish yellow/graphite Settings.

Apply strictly to the verified PRE117 source. This module does not touch a
persistent workspace; patching occurs inside a temporary GitHub runner.
"""
from __future__ import annotations
import hashlib
EXPECTED_PRE117_SHA="8fa1f89c29e59cd96234d1ccaf18d9ff72baab790449b9e84151eac7c64794af"

def replace_one(src:str,old:str,new:str,label:str)->str:
    if src.count(old)!=1:
        raise ValueError("PRE128 anchor count invalid: "+label)
    return src.replace(old,new,1)

def propose(pre117:str)->str:
    if hashlib.sha256(pre117.encode("utf-8")).hexdigest()!=EXPECTED_PRE117_SHA:
        raise ValueError("PRE128 rejects source not equal to exact PRE117")
    result=pre117
    result=replace_one(result,
        "void SettingsDialog::OnDraw(ImGuiIO& /*io*/) {",
        "void SettingsDialog::OnDraw(ImGuiIO& io) {",
        "enable mouse delta")
    result=replace_one(result,
        "    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);\n  }\n\n  const bool settings_visible",
        """    ImGui::PushStyleVar(ImGuiStyleVar_WindowRounding, 16.0f);
    // PRE128: root scrollbar is rendered during Begin(), so colors must
    // be pushed BEFORE Begin(), not in the form contents.
    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarBg,
        ImVec4(0.11f, 0.12f, 0.13f, 0.86f));
    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarGrab,
        ImVec4(0.66f, 0.52f, 0.07f, 1.0f));
    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarGrabHovered,
        ImVec4(0.89f, 0.69f, 0.05f, 1.0f));
    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarGrabActive,
        ImVec4(1.00f, 0.82f, 0.05f, 1.0f));
  }

  const bool settings_visible""",
        "root scrollbar colors before Begin")
    result=replace_one(result,
        """      ImGuiWindowFlags_NoCollapse |
      ImGuiWindowFlags_NoMove |
      ImGuiWindowFlags_NoResize);""",
        """      ImGuiWindowFlags_NoCollapse |
      ImGuiWindowFlags_NoMove |
      ImGuiWindowFlags_NoResize |
      (mobile_layout ? ImGuiWindowFlags_NoTitleBar : 0));""",
        "hide redundant green legacy titlebar on Android")
    result=replace_one(result,
        """  if (mobile_layout) {
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(2);
  }

  if (!settings_visible) {""",
        """  if (mobile_layout) {
    ImGui::PopStyleVar();
    ImGui::PopStyleColor(6);  // 2 existing + 4 root scrollbar overrides.
  }

  if (!settings_visible) {""",
        "root style stack balance")
    result=replace_one(result,
        """        ImGuiCol_TitleBgActive,
        ImVec4(0.14f, 0.14f, 0.12f, 1.0f));
  }

  if (mobile_layout) {""",
        """        ImGuiCol_TitleBgActive,
        ImVec4(0.14f, 0.14f, 0.12f, 1.0f));
    // PRE128: cover the remaining inherited green ImGui colors.
    ImGui::PushStyleColor(
        ImGuiCol_ScrollbarBg,
        ImVec4(0.11f, 0.12f, 0.13f, 0.86f));
    ImGui::PushStyleColor(
        ImGuiCol_SliderGrabActive,
        ImVec4(1.00f, 0.82f, 0.08f, 1.0f));
    ImGui::PushStyleColor(
        ImGuiCol_TextSelectedBg,
        ImVec4(0.95f, 0.73f, 0.05f, 0.28f));
    ImGui::PushStyleColor(
        ImGuiCol_SeparatorHovered,
        ImVec4(0.85f, 0.69f, 0.07f, 1.0f));
    ImGui::PushStyleColor(
        ImGuiCol_SeparatorActive,
        ImVec4(0.95f, 0.78f, 0.08f, 1.0f));
  }

  if (mobile_layout) {""",
        "finish ImGui colors scoped to Settings")
    result=replace_one(result,
        """  ImGui::PopStyleColor(mobile_layout ? 20 : 11);
  ImGui::PopStyleVar(4);
  ImGui::End();""",
        """  // PRE128: an Android finger is reported by SDL as a primary mouse drag.
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
  ImGui::End();""",
        "safe Android drag scroll, style stack balance")
    if result.count("PRE117: Android uses the root Settings window as the sole scroll owner.")!=1:
        raise ValueError("PRE128 must preserve PRE117 scroll-owner fix")
    if result.count('ImGui::BeginChild("##cvars"')!=1:
        raise ValueError("PRE128 CVar layout invariants changed")
    if result.count('ImGui::PopStyleColor(6)')!=1 or result.count('ImGui::PopStyleColor(mobile_layout ? 25 : 11)')!=1:
        raise ValueError("PRE128 style pop count invalid")
    return result
