#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 네트워크/입력 설정
UDP_HOST = "127.0.0.1"
UDP_PORT = 8000
UDP_TIMEOUT_SEC = 0.03
SMOOTHING_FACTOR = 0.12

# 실행 모드
# - "udp_text": /address:value 형태 UDP 텍스트 수신 (현재 OSCRouter 사용)
# - "td_chop": TouchDesigner OSC In CHOP 값을 직접 읽음 (공연 안정성 높음)
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

# SceneManager 기본값
BASE_NOISE_AMP = 0.10
BASE_TRAIL_SECONDS = 0.35
BASE_FORCE_OUT = 0.70

NOISE_AMP_RANGE = (0.05, 0.35)
TRAIL_SECONDS_RANGE = (0.20, 0.90)
FORCE_OUT_RANGE = (0.40, 1.20)

# TouchDesigner 오퍼레이터 매핑 (반드시 네 프로젝트 경로로 교체)
OP_MAP = {
    "noise_amp": {"op": "/project1/pop_noise", "par": "amplitude"},
    "trail_seconds": {"op": "/project1/pop_trail", "par": "trailseconds"},
    "force_out_strength": {"op": "/project1/pop_force_out", "par": "strength"},
}
