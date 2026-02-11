#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Any, List
from td_scripts import config

# 최근 적용값 캐시 (변화량 기반 apply 최적화)
_LAST_APPLIED: Dict[str, float] = {}


def _get_td_op(op_path: str):
    """
    TD 내장 op() 접근
    TD 외부에서는 None
    """
    try:
        fn = globals().get("op", None)
        if fn is None:
            return None
        return fn(op_path)
    except Exception:
        return None


def _get_par(operator, par_name: str):
    try:
        return operator.par[par_name]
    except Exception:
        return getattr(operator.par, par_name, None)


def _read_current_value(par):
    try:
        return float(par.eval())
    except Exception:
        try:
            return float(par.val)
        except Exception:
            return None


def set_td_par(op_path: str, par_name: str, value: float, epsilon: float = config.EPSILON) -> Dict[str, Any]:
    """
    TD 파라미터 안전 적용 + 변화량이 작으면 생략
    """
    key = f"{op_path}.{par_name}"
    target = float(value)

    operator = _get_td_op(op_path)
    if operator is None:
        return {"ok": False, "applied": False, "message": f"operator not found or TD env missing: {op_path}"}

    par = _get_par(operator, par_name)
    if par is None:
        return {"ok": False, "applied": False, "message": f"parameter not found: {op_path}.{par_name}"}

    # 1) 캐시 비교
    prev = _LAST_APPLIED.get(key, None)
    if prev is not None and abs(target - prev) < float(epsilon):
        return {"ok": True, "applied": False, "message": f"skip tiny change: {key}"}

    # 2) 실제 현재값 비교 (첫 적용 시)
    if prev is None:
        current = _read_current_value(par)
        if current is not None and abs(target - current) < float(epsilon):
            _LAST_APPLIED[key] = current
            return {"ok": True, "applied": False, "message": f"skip unchanged: {key}"}

    try:
        par.val = target
        _LAST_APPLIED[key] = target
        return {"ok": True, "applied": True, "message": f"set {key}={target:.4f}"}
    except Exception as e:
        return {"ok": False, "applied": False, "message": f"failed to set {key}: {e}"}


def apply_params_to_td(params: Dict[str, float], op_map: Dict[str, Dict[str, str]], epsilon: float = config.EPSILON) -> Dict[str, Any]:
    """
    반환 구조 고정:
    {
      "ok": bool,
      "changed": List[str],
      "warnings": List[str],
      "errors": List[str]
    }
    """
    changed: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []

    if not isinstance(params, dict):
        return {"ok": False, "changed": changed, "warnings": warnings, "errors": ["params must be dict"]}
    if not isinstance(op_map, dict):
        return {"ok": False, "changed": changed, "warnings": warnings, "errors": ["op_map must be dict"]}

    for param_key, param_val in params.items():
        mapping = op_map.get(param_key)
        if mapping is None:
            warnings.append(f"no mapping for: {param_key}")
            continue

        # 두 형태 모두 지원
        op_path = mapping.get("op_path") or mapping.get("op")
        par_name = mapping.get("par_name") or mapping.get("par")

        if not op_path or not par_name:
            warnings.append(f"incomplete mapping for: {param_key}")
            continue

        res = set_td_par(op_path, par_name, float(param_val), epsilon=epsilon)

        if res["ok"] and res.get("applied", False):
            changed.append(f"{param_key} -> {op_path}.{par_name}={float(param_val):.4f}")
        elif res["ok"] and not res.get("applied", False):
            # 미세 변화 스킵은 경고가 아니라 정상 동작
            pass
        else:
            msg = res.get("message", "unknown error")
            if ("not found" in msg.lower()) or ("missing" in msg.lower()):
                warnings.append(msg)
            else:
                errors.append(msg)

    return {"ok": len(errors) == 0, "changed": changed, "warnings": warnings, "errors": errors}
