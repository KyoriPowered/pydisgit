"""
ASGI middleware to verify HMAC signatures from GH
"""

import hmac
import logging
from collections.abc import Callable
from hypercorn.typing import Scope

logger = logging.getLogger(__name__)


class HmacVerifyMiddleware:
  """
  Middleware to verify HMAC signatures inserted by GitHub.
  """

  def __init__(self, app, hmac_secret) -> None:
    self.app = app
    self.__hmac_secret = hmac_secret.encode() if hmac_secret else None

  async def __call__(self, scope: Scope, receive: Callable, send: Callable) -> None:
    if (
      self.__hmac_secret is None
      or scope["type"] != "http"
      or len(scope["path"]) <= len("/health")
    ):
      await self.app(scope, receive, send)
      return

    # processing an http connection
    signature_header = None
    for k, v in scope["headers"]:
      if k.lower() == b"x-hub-signature-256":
        signature_header = v
        break

    if signature_header is None:
      await self.__error_response__(receive, send, "No signature provided")
      return

    digest = hmac.new(key=self.__hmac_secret, digestmod="sha256")
    await self.app(
      scope,
      self.recv_proxy(digest, signature_header[len("sha256=") :], receive, send),
      send,
    )

  def recv_proxy(
    self, digest: hmac.HMAC, expected: bytes, recv: Callable, send: Callable
  ) -> Callable:
    async def responder() -> dict:
      response = await recv()
      if response["type"] == "http.request":
        digest.update(response["body"])
        if not response["more_body"]:
          result = digest.hexdigest().encode()
          if result != expected:
            # send error response
            logger.debug(
              "Hash mismatch on request, got %s but expected %s", result, expected
            )
            await self.__error_response__(
              recv, send, "Hash digest did not match expected"
            )
            return {"type": "http.disconnect"}
      return response

    return responder

  async def __error_response__(
    self, recv: Callable, send: Callable, message: str
  ) -> None:
    bstr = message.encode()
    await send(
      {
        "type": "http.response.start",
        "status": 403,
        "headers": [(b"content-length", str(len(bstr)).encode())],
      }
    )
    await send(
      {
        "type": "http.response.body",
        "body": bstr,
        "more_body": False,
      }
    )
