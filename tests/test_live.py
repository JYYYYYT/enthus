"""Synthetic P1 replays; no microphone, live model, or experience claim."""

from __future__ import annotations

import asyncio
import base64
import time
import unittest
from unittest.mock import patch
from typing import Any

from aiohttp import ClientWebSocketResponse, web
from aiohttp.test_utils import TestClient, TestServer

from enthus.live import create_app
from enthus.live_session import LiveLimits, LiveSession, SessionEnded


def audio_output() -> dict[str, Any]:
    return {"serverContent": {"modelTurn": {"parts": [{"inlineData": {
        "mimeType": "audio/pcm;rate=24000", "data": base64.b64encode(bytes(4800)).decode()
    }}]}}}


def observation(sensor: str = "audio") -> dict[str, Any]:
    raw = bytes(3200) if sensor == "audio" else b"\xff\xd8synthetic-jpeg"
    return {"type": "media", "sensor": sensor, "captured_at": time.time(),
            "data": base64.b64encode(raw).decode()}


class SessionTests(unittest.TestCase):
    def test_s26_turn_completion_keeps_perception_active(self) -> None:
        state = LiveSession()
        state.provider_message({"serverContent": {"turnComplete": True}})
        self.assertIsNotNone(state.observation(observation("video")))
        self.assertTrue(state.active)
        self.assertEqual(state.versions["video"], 1)

    def test_s28_late_audio_cannot_revive_cancelled_turn(self) -> None:
        state = LiveSession()
        first = state.provider_message(audio_output())[0]
        state.stop_speech([first["output_id"]])
        self.assertEqual(state.provider_message(audio_output())[0]["kind"], "discarded")
        state.provider_message({"serverContent": {"turnComplete": True}})
        self.assertEqual(state.provider_message(audio_output())[0]["kind"], "audio")

    def test_s31_revoking_video_preserves_audio_but_end_revokes_all(self) -> None:
        state = LiveSession()
        state.revoke("video")
        self.assertIsNone(state.observation(observation("video")))
        self.assertIsNotNone(state.observation(observation()))
        state.stop("user_ended")
        with self.assertRaises(SessionEnded):
            state.observation(observation())
        with self.assertRaises(SessionEnded):
            state.provider_message(audio_output())
        self.assertFalse(any(state.grants.values()))

    def test_stale_input_never_reaches_model(self) -> None:
        state = LiveSession()
        item = observation()
        item["captured_at"] -= 2
        self.assertIsNone(state.observation(item))
        self.assertEqual(state.audio_bytes, 0)

    def test_s32_media_duration_and_output_bounds(self) -> None:
        state = LiveSession(LiveLimits(input_audio_bytes=3200, output_audio_bytes=4800))
        state.observation(observation())
        with self.assertRaisesRegex(SessionEnded, "input_audio_limit"):
            state.observation(observation())
        state.provider_message(audio_output())
        with self.assertRaisesRegex(SessionEnded, "output_audio_limit"):
            state.provider_message(audio_output())
        state.started -= 121
        with self.assertRaisesRegex(SessionEnded, "duration_limit"):
            state.require_active()

    def test_provider_interrupt_invalidates_all_parts_in_same_event(self) -> None:
        state = LiveSession()
        message = audio_output()
        message["serverContent"]["interrupted"] = True
        self.assertEqual([e["kind"] for e in state.provider_message(message)],
                         ["interrupted", "discarded"])

    def test_frame_rate_and_metadata_only_trace(self) -> None:
        state = LiveSession()
        state.observation(observation("video"))
        self.assertIsNone(state.observation(observation("video")))
        state.provider_message(audio_output())
        self.assertTrue(all("data" not in event for event in state.trace))


class BridgeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.received: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.provider: web.WebSocketResponse | None = None

        async def provider(request: web.Request) -> web.WebSocketResponse:
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            self.provider = ws
            await self.received.put(await ws.receive_json())
            await ws.send_json({"setupComplete": {}})
            async for msg in ws:
                await self.received.put(msg.json())
            return ws

        app = web.Application()
        app.router.add_get("/provider", provider)
        self.upstream = TestServer(app)
        await self.upstream.start_server()
        self.endpoint = patch("enthus.live.ENDPOINT", str(self.upstream.make_url("/provider")))
        self.endpoint.start()
        self.client = TestClient(TestServer(create_app("synthetic-secret")))
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()
        await self.upstream.close()
        self.endpoint.stop()

    async def start_session(self) -> ClientWebSocketResponse:
        config = await (await self.client.get("/config")).json()
        ws = await self.client.ws_connect("/session", headers={
            "Origin": str(self.client.make_url("/")).rstrip("/")})
        await ws.send_json({"type": "start", "token": config["token"], "audio": True, "video": True})
        self.assertEqual((await ws.receive_json(timeout=2))["kind"], "connecting")
        self.assertEqual((await ws.receive_json(timeout=2))["kind"], "ready")
        setup = await asyncio.wait_for(self.received.get(), 2)
        self.assertIn("setup", setup)
        return ws

    async def test_s26_s31_actual_bridge_with_synthetic_provider(self) -> None:
        ws = await self.start_session()
        await self.provider.send_json({"serverContent": {"turnComplete": True}})
        self.assertEqual((await ws.receive_json(timeout=2))["kind"], "turn_complete")
        await ws.send_json(observation("video"))
        data = await asyncio.wait_for(self.received.get(), 2)
        self.assertIn("video", data["realtimeInput"])
        await ws.send_json({"type": "stop_sensor", "sensor": "video"})
        self.assertEqual((await ws.receive_json(timeout=2))["kind"], "revoked")
        await ws.send_json(observation("video"))
        await ws.send_json(observation())
        data = await asyncio.wait_for(self.received.get(), 2)
        self.assertIn("audio", data["realtimeInput"])
        await ws.send_json({"type": "end"})
        ended = await ws.receive_json(timeout=2)
        self.assertEqual(ended["reason"], "user_ended")
        self.assertNotIn("synthetic-secret", str(ended))
        self.assertTrue(any(e["kind"] == "dropped" for e in ended["trace"]))

    async def test_s32_provider_disconnect_visible_and_new_host_idle(self) -> None:
        ws = await self.start_session()
        await self.provider.close()
        event = await ws.receive_json(timeout=2)
        self.assertEqual(event["reason"], "provider_disconnected")
        await ws.close()
        self.assertTrue(self.received.empty())
        config = await (await self.client.get("/config")).json()
        self.assertTrue(config["configured"])
        self.assertTrue(self.received.empty())  # Reading state never starts a model session.

    async def test_cross_origin_and_missing_grants_cannot_connect_model(self) -> None:
        response = await self.client.get("/session", headers={"Origin": "https://foreign.example"})
        self.assertEqual(response.status, 403)
        self.assertIsNone(self.provider)
        ws = await self.client.ws_connect("/session", headers={
            "Origin": str(self.client.make_url("/")).rstrip("/")})
        await ws.send_json({"type": "start", "audio": True, "video": True})
        self.assertEqual((await ws.receive_json(timeout=2))["reason"], "invalid_start_grant")
        self.assertIsNone(self.provider)
        await ws.close()


if __name__ == "__main__":
    unittest.main()
