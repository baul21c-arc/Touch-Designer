#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 네트워크/입력 설정 (udp_text 모드용)
UDP_HOST = "127.0.0.1"
UDP_PORT = 8000
UDP_TIMEOUT_SEC = 0.03
SMOOTHING_FACTOR = 0.12

# 실행 모드
# - "udp_text": /address:value 형태 UDP 텍스트 수신 (OSCRouter 사용)
# - "td_chop": TouchDesigner OSC In CHOP 값을 직접 읽음
INPUT_MODE = "udp_text"

# td_chop 모드일 때 사용할 CHOP 경로/채널명 매핑
OSC_CHOP_PATH = "/project1/osc_in1"
CHOP_CHANNEL_MAP = {
    "/phase": "phase",
    "/audio/bass_rms": "bass_rms",
    "/audio/noise_rms": "noise_rms",
    "/sensor/contact": "contact",
}

# 디버그/안전값
DEBUG = False
EPSILON = 0.0005  # 값 변화가 이보다 작으면 apply 생략

# TouchDesigner 오퍼레이터 매핑 (반드시 네 프로젝트 경로로 교체)
OP_MAP = {
    "noise_amp": {
        "op_path": "/project1/pop_test_params",
        "par_name": "const0value0",
        "min": 0.05,
        "max": 0.35,
    },
    "trail_seconds": {
        "op_path": "/project1/pop_test_params",
        "par_name": "const1value1",
        "min": 0.20,
        "max": 0.90,
    },
    "force_out_strength": {
        "op_path": "/project1/pop_test_params",
        "par_name": "const2value2",
        "min": 0.40,
        "max": 1.20,
    },
}
