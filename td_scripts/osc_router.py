#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from typing import Dict, Any
from td_scripts import config


class OSCRouter:
    """
    UDP 텍스트 메시지 '/address:value' 수신 라우터
    예) /audio/bass_rms:0.38
    """

    ALLOWED = {
        "/phase": (0.0, 1.0),
        "/audio/bass_rms": (0.0, 1.0),
        "/audio/noise_rms": (0.0, 1.0),
        "/sensor/contact": (0.0, 1.0),
    }

    def __init__(
        self,
        host: str = config.UDP_HOST,
        port: int = config.UDP_PORT,
        smoothing_factor: float = config.SMOOTHING_FACTOR,
        timeout_sec: float = config.UDP_TIMEOUT_SEC,
        debug: bool = config.DEBUG,
    ):
        self.host = host
        self.port = int(port)
        self.alpha = max(0.0, min(1.0, float(smoothing_factor)))
        self.debug = bool(debug)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(float(timeout_sec))

        self.values: Dict[str, float] = {k: 0.0 for k in self.ALLOWED.keys()}

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, float(v)))

    def _normalize(self, addr: str, raw: float) -> float:
        lo, hi = self.ALLOWED[addr]
        # 이 프로젝트는 기본 0~1 입력 가정 + 안전 클램프
        return self._clamp(raw, lo, hi)

    @staticmethod
    def _parse_message(data: bytes):
        text = data.decode("utf-8").strip()
        if ":" not in text:
            raise ValueError(f"invalid format: {text}")
        addr, val = text.split(":", 1)
        return addr.strip(), float(val.strip())

    def _smooth(self, old: float, new: float) -> float:
        return old + (new - old) * self.alpha

    def process_one(self) -> Dict[str, Any]:
        """
        메시지 1건 처리
        """
        result = {"ok": True, "changed": [], "warnings": [], "errors": []}

        try:
            data, _ = self.sock.recvfrom(2048)
        except socket.timeout:
            return result
        except Exception as e:
            result["ok"] = False
            result["errors"].append(f"socket receive error: {e}")
            return result

        try:
            addr, raw = self._parse_message(data)
        except Exception as e:
            result["ok"] = False
            result["errors"].append(f"parse error: {e}")
            return result

        if addr not in self.ALLOWED:
            result["warnings"].append(f"ignored address: {addr}")
            return result

        try:
            norm = self._normalize(addr, raw)
            old = self.values.get(addr, 0.0)
            smoothed = self._smooth(old, norm)
            self.values[addr] = smoothed
            result["changed"].append(f"{addr}={smoothed:.4f}")

            if self.debug:
                print(f"[OSC] {addr} raw={raw:.4f} norm={norm:.4f} smooth={smoothed:.4f}")
        except Exception as e:
            result["ok"] = False
            result["errors"].append(f"process error: {e}")

        return result

    def get_status(self) -> Dict[str, float]:
        return {k: float(self.values.get(k, 0.0)) for k in self.ALLOWED.keys()}

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass
