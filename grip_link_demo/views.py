import time
from urllib.parse import urljoin
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views import View
from django_grip import set_hold_stream, publish
from gripcontrol import Channel, HttpStreamFormat


class SSESpecializedChannelView(View):
    def get(self, request: HttpRequest, channel_uuid: str) -> HttpResponse:
        resp = HttpResponse(content_type="text/event-stream")
        resp.headers["X-Accel-Buffering"] = "no"  # disable nginx buffering

        channel = Channel(channel_uuid, prev_id=0)
        set_hold_stream(
            request,
            channel,
            keep_alive_data=":keepalive\n; format=cstring",
            keep_alive_timeout=20,
        )
        next_link = urljoin("http://localhost:8000", reverse("streaming-is-expired-channel"))
        request.grip.instruct.set_next_link(next_link, timeout=30)  # type:ignore[attr-defined]
        return resp


class SSEIsExpiredView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        resp = HttpResponse(content_type="text/event-stream")
        resp.headers["X-Accel-Buffering"] = "no"  # disable nginx buffering

        print(request.headers)
        if "Grip-Last" not in request.headers:
            raise Exception("No Grip-Last header in request")

        channel_str = (request.headers["Grip-Last"] or "").split(";")[0]
        if channel_is_expired(channel_str):
            return resp

        channel = Channel(channel_str, prev_id=0)
        set_hold_stream(
            request,
            channel,
            keep_alive_data=":keepalive\n; format=cstring",
            keep_alive_timeout=20,
        )
        next_link = urljoin("http://localhost:8000", reverse("streaming-is-expired-channel"))
        request.grip.instruct.set_next_link(next_link, timeout=30)  # type:ignore[attr-defined]
        return resp


class SSEGenerateMessages(View):
    def get(self, request: HttpRequest, channel_uuid: str) -> HttpResponse:
        for i in range(10):
            message = f"messaggio {i}"
            prev_id = "0"
            print(f"Send {i} to {channel_uuid}")
            publish(channel_uuid, HttpStreamFormat(message), prev_id=prev_id)
            time.sleep(2)

        return HttpResponse("OK")


def channel_is_expired(channel):
    return False
