#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Any
from td_scripts import config
from td_scripts.osc_router import OSCRouter
from td_scripts.scene_manager import SceneManager
from td_scripts.td_apply import apply_params_to_td

_router = None
_scene = None
_last_error = None


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def _ensure_init():
    global _router, _scene
    if _scene is None:
        _scene = SceneManager()

    if config.INPUT_MODE == "udp_text":
        if _router is None:
            _router = OSCRouter(
                host=config.UDP_HOST,
                port=config.UDP_PORT,
                smoothing_factor=config.SMOOTHING_FACTOR,
                timeout_sec=config.UDP_TIMEOUT_SEC,
                debug=config.DEBUG,
            )


def _get_status_from_td_chop() -> Dict[str, float]:
    """
    td_chop 모드: OSC In CHOP 값을 직접 읽어 상태 딕셔너리로 변환
    """
    status = {k: 0.0 for k in config.CHOP_CHANNEL_MAP.keys()}

    try:
        op_func = globals().get("op", None)
        if op_func is None:
            return status

        chop = op_func(config.OSC_CHOP_PATH)
        if chop is None:
            return status

        for osc_addr, ch_name in config.CHOP_CHANNEL_MAP.items():
            try:
                ch = chop[ch_name]
                # CHOP 채널 최신 샘플
                v = float(ch[-1]) if len(ch) > 0 else float(ch.eval())
                status[osc_addr] = _clamp01(v)
            except Exception:
                status[osc_addr] = 0.0
    except Exception:
        pass

    return status


def tick() -> Dict[str, Any]:
    """
    프레임마다 호출:
      1) 입력 수집(udp_text 또는 td_chop)
      2) 파라미터 계산
      3) TD 적용
    """
    global _last_error
    _ensure_init()

    osc_res = {"ok": True, "changed": [], "warnings": [], "errors": []}
    try:
        if config.INPUT_MODE == "udp_text":
            osc_res = _router.process_one()
            osc_status = _router.get_status()
        else:
            osc_status = _get_status_from_td_chop()
    except Exception as e:
        _last_error = str(e)
        return {
            "ok": False,
            "changed": [],
            "warnings": [],
            "errors": [f"input stage error: {e}"],
            "osc_status": {},
            "computed_params": {},
            "applied_count": 0,
            "mode": config.INPUT_MODE,
            "last_error": _last_error,
        }

    calc = _scene.compute_parameters(osc_status)
    if not calc.get("ok", False):
        _last_error = "; ".join(calc.get("errors", [])) if calc.get("errors") else "compute failed"
        return {
            "ok": False,
            "changed": [],
            "warnings": osc_res.get("warnings", []) + calc.get("warnings", []),
            "errors": osc_res.get("errors", []) + calc.get("errors", []),
            "osc_status": osc_status,
            "computed_params": {},
            "applied_count": 0,
            "mode": config.INPUT_MODE,
            "last_error": _last_error,
        }

    apply_res = apply_params_to_td(calc.get("params", {}), config.OP_MAP, epsilon=config.EPSILON)
    errors = osc_res.get("errors", []) + calc.get("errors", []) + apply_res.get("errors", [])
    warnings = osc_res.get("warnings", []) + calc.get("warnings", []) + apply_res.get("warnings", [])
    changed = apply_res.get("changed", [])
    _last_error = errors[-1] if errors else None

    return {
        "ok": len(errors) == 0,
        "changed": changed,
        "warnings": warnings,
        "errors": errors,
        "osc_status": osc_status,
        "computed_params": calc.get("params", {}),
        "applied_count": len(changed),
        "mode": config.INPUT_MODE,
        "last_error": _last_error,
    }


if __name__ == "__main__":
    # TD 밖에서 import/문법 확인용
    print("runtime_loop smoke: import OK")
