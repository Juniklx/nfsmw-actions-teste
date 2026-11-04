#!/usr/bin/env python3
"""PRE133: remove unreachable native touch-id gate from Android Settings swipe.

PRE130 proved SDL WindowSDL routes SDL mouse events, not finger events, to the
ImGuiDrawer. PRE131's IsTouchPointerActive depended on OnTouchEvent, which may
never be called by that SDL route. Use io.MouseDown/MousePos (used by scrollbar)
without changing font, style, CVARs, desktop or physical controls.
"""
from __future__ import annotations
import hashlib
PRE131_SHA="9e95ab6637ec742be5d2f0d9aca94c8ce4f5f4f19f93ec94700183699b23ece7"

def propose(v29_source:bytes)->bytes:
    if hashlib.sha256(v29_source).hexdigest()!=PRE131_SHA:
        raise ValueError("PRE133 expects exact PRE131 Settings C++ source")
    code=v29_source.decode("utf-8")
    old="""  // PRE131: the native ImGuiDrawer::OnTouchEvent stores the finger in
  // io.MousePos/io.MouseDown, but ImGui::IsMouseDragging and hovered-window
  // checks from PRE128 did not scroll on the S24 FE (observed on V28).
  // Track that real native touch pointer explicitly and scroll the ROOT only.
  // A touch beginning on an interactive control still belongs to that control.
  if (mobile_layout) {
    const bool finger_down =
        imgui_drawer()->IsTouchPointerActive() && io.MouseDown[0];"""
    new="""  // PRE133: Android SDL3 delivers touchscreen movement as mouse input in
  // WindowSDL::HandleMouseEvent. OnTouchEvent is not dispatched by that path.
  // The PRE131 IsTouchPointerActive() gate remained false on the S24 FE.
  // Use the primary pointer state already used by working scrollbar dragging.
  // Keep the single ROOT scroll owner and never intercept a control active
  // when the drag starts.
  if (mobile_layout) {
    const bool finger_down =
        io.MouseDown[0] &&
        std::isfinite(io.MousePos.x) && std::isfinite(io.MousePos.y);"""
    if code.count(old)!=1:
        raise ValueError("PRE133 source anchor mismatch")
    code=code.replace(old,new,1)
    if "imgui_drawer()->IsTouchPointerActive()" in code:
        raise ValueError("PRE133 touch pointer gate still present")
    if code.count("PRE117: Android uses the root Settings window as the sole scroll owner.")!=1:
        raise ValueError("PRE117 root scroll invariant lost")
    if code.count("ImGui::SetScrollY(clamped);")!=1:
        raise ValueError("PRE133 drag scroll call changed")
    if code.count('ImGui::PopStyleColor(mobile_layout ? 25 : 11);')!=1:
        raise ValueError("Style stack changed")
    return code.encode("utf-8")
