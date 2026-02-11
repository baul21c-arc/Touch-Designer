#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from typing import Dict, Any, List
from td_scripts import config


class SceneManager:
    """
    정규화된 OSC 상태값 -> TD 파라미터 매핑
    """

    def __init__(
        self,
        base_noise_amp: float = config.BASE_NOISE_AMP,
        base_trail_seconds: float = config.BASE_TRAIL_SECONDS,
        base_force_out: float = config.BASE_FORCE_OUT,
    ):
        self.base_noise_amp = float(base_noise_amp)
        self.base_trail_seconds = float(base_trail_seconds)
        self.base_force_out = float(base_force_out)

        self.noise_amp_range = tuple(config.NOISE_AMP_RANGE)
        self.trail_seconds_range = tuple(config.TRAIL_SECONDS_RANGE)
        self.force_out_range = tuple(config.FORCE_OUT_RANGE)

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, float(v)))

    def _safe_norm(self, value: Any, key: str, warnings: List[str]) -> float:
        try:
            v = float(value)
        except Exception:
            warnings.append(f"{key} non-numeric -> 0.0")
            return 0.0
        if not math.isfinite(v):
            warnings.append(f"{key} NaN/Inf -> 0.0")
            return 0.0
        return self._clamp(v, 0.0, 1.0)

    def compute_parameters(self, osc_status: Dict[str, Any]) -> Dict[str, Any]:
        warnings: List[str] = []
        errors: List[str] = []

        try:
            phase = self._safe_norm(osc_status.get("/phase", 0.0), "/phase", warnings)
            bass = self._safe_norm(osc_status.get("/audio/bass_rms", 0.0), "/audio/bass_rms", warnings)
            noise = self._safe_norm(osc_status.get("/audio/noise_rms", 0.0), "/audio/noise_rms", warnings)
            contact = self._safe_norm(osc_status.get("/sensor/contact", 0.0), "/sensor/contact", warnings)
        except Exception as e:
            return {"ok": False, "params": {}, "warnings": warnings, "errors": [f"status read error: {e}"]}

        try:
            # phase는 장면 강도 보정에 사용
            phase_gain = 0.65 if phase < 0.5 else 1.0

            noise_amp = (self.base_noise_amp + contact * 0.14 + noise * 0.10) * phase_gain
            trail_seconds = (self.base_trail_seconds + contact * 0.30) * phase_gain
            force_out_strength = (self.base_force_out + bass * 0.40) * phase_gain

            noise_amp = self._clamp(noise_amp, *self.noise_amp_range)
            trail_seconds = self._clamp(trail_seconds, *self.trail_seconds_range)
            force_out_strength = self._clamp(force_out_strength, *self.force_out_range)
        except Exception as e:
            errors.append(f"parameter compute error: {e}")
            return {"ok": False, "params": {}, "warnings": warnings, "errors": errors}

        return {
            "ok": True,
            "params": {
                "noise_amp": noise_amp,
                "trail_seconds": trail_seconds,
                "force_out_strength": force_out_strength,
            },
            "warnings": warnings,
            "errors": errors,
        }


if __name__ == "__main__":
    sm = SceneManager()
    sample = {
        "/phase": 0.8,
        "/audio/bass_rms": 0.7,
        "/audio/noise_rms": 0.3,
        "/sensor/contact": 0.5,
    }
    print(sm.compute_parameters(sample))
