import time
from urllib.parse import urljoin

from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.views import View
from django.utils import timezone
from django_grip import publish, set_hold_stream
from gripcontrol import Channel, HttpStreamFormat


# MODE = 0  # no prev id, does not work
MODE = 1  # always 0 as prev id, does not work when a message is sent and received before the first is-expired call
# MODE = 2  # set sequence id and prev id, works


LAST_KNOWN_ID = None
def update_last_known_id(id_):
    global LAST_KNOWN_ID
    LAST_KNOWN_ID = id_

CHANNELS_START_TIME = {}
def update_start_time(channel_str):
    global CHANNELS_START_TIME
    CHANNELS_START_TIME[channel_str] = timezone.now()

class SSESpecializedChannelView(View):
    def get(self, request: HttpRequest, channel_uuid: str) -> HttpResponse:
        resp = HttpResponse(content_type="text/event-stream")

        prev_id = None if MODE == 0 else "0"
        update_last_known_id(prev_id)
        channel = Channel(channel_uuid, prev_id=prev_id)
        set_hold_stream(
            request,
            channel,
            keep_alive_data=":keepalive\n; format=cstring",
            keep_alive_timeout=20,
        )
        next_link = urljoin("http://localhost:8000", reverse("streaming-is-expired-channel"))
        request.grip.instruct.set_next_link(next_link, timeout=30)  # type:ignore[attr-defined]
        update_start_time(channel_uuid)
        return resp


class SSEIsExpiredView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        resp = HttpResponse(content_type="text/event-stream")

        if "Grip-Last" not in request.headers:
            raise Exception("No Grip-Last header in request")

        channel_str = (request.headers["Grip-Last"] or "").split(";")[0]
        if channel_is_expired(channel_str):
            return resp

        channel = Channel(channel_str, prev_id=LAST_KNOWN_ID)
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
        publish_messages(channel_uuid)
        return HttpResponse("OK")


def channel_is_expired(channel):
    channel_start_time = CHANNELS_START_TIME.get(channel)
    return channel_start_time is not None and (timezone.now() - channel_start_time).total_seconds() > 60


def publish_messages(channel_uuid):
    text = "Here is a streaming message".split()

    for i, tok in enumerate(text):
        message = "\n".join([f"data: {tok}", "", ""])
        if MODE == 0:
            prev_id = None
            id_ = None
        elif MODE == 1:
            prev_id = "0"
            id_ = None
        else:
            prev_id = str(i)
            id_ = str(i+1)
            update_last_known_id(id_)

        print(f"> Send {tok}, id_ {id_}, prev_id {prev_id}")
        publish(channel_uuid, HttpStreamFormat(message + "\n"), prev_id=prev_id, id=id_)
        time.sleep(2)
