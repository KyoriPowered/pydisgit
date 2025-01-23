"""
Core logic for webhook handling
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from logging import Logger
from typing import Any, Optional, NamedTuple
import inspect

from .conf import BoundEnv
from .util import truncate


class Sender(NamedTuple):
  """
  GH API Sender representation
  """
  login: str
  html_url: str
  avatar_url: str

  @classmethod
  def from_json(cls, data: Any):
    return cls(data["login"], data["html_url"], data["avatar_url"])

class Field(NamedTuple):
  """
  Discord API field representation
  """
  name: str
  value: str
  inline: bool = True

  def to_json(self) -> Any:
    """
    Return a JSON representation of this field for sending to discord
    """
    return {
      "name": self.name,
      "value": truncate(self.value, 1000),
      "inline": self.inline
    }

@dataclass
class EmbedBody:
  """
  Discord API embed representation
  """
  title: str
  url: Optional[str]
  sender: Sender
  color: int
  description: Optional[str] = None
  footer: Optional[str] = None
  fields: list[Field] = field(default_factory=lambda: [])

  def __post_init__(self):
    if not isinstance(self.sender, Sender):
      self.sender = Sender.from_json(self.sender)

  def to_json(self) -> Any:
    return {
      "embeds": [
        {
          "title": truncate(self.title, 255),
          "url": self.url,
          "description": truncate(self.description, 1000) if self.description else None,
          "author": {
            "name": truncate(self.sender.login, 255),
            "url": self.sender.html_url,
            "icon_url": self.sender.avatar_url
          },
          "color": self.color,
          "footer": {
            "text": truncate(self.footer, 255),
          } if self.footer else None,
          "fields": [f.to_json() for f in self.fields],
        }
      ]
    }


type EventHandler = Callable[[BoundEnv, dict], Optional[EmbedBody]]

class BoundRouter:

  def __init__(self, handlers: dict[str, EventHandler], env: BoundEnv, logger: Logger):
    self._handlers = handlers
    self._env = env
    self._logger = logger

  def process_request(self, gh_hook_type: str, gh_data: dict) -> Optional[Any]:
    """
    Process the request based on the hook types
    """
    if self._env.ignored_payload(gh_hook_type):
      self._logger.info("Ignoring payload type %s", gh_hook_type)
      return None

    if gh_hook_type not in self._handlers:
      self._logger.debug("No handler for %s", gh_hook_type)
      return None

    result = self._handlers[gh_hook_type](self._env, gh_data)
    if not result:
      self._logger.debug("Produced no result for event type '%s' with payload '%s", gh_hook_type, gh_data)
      return None

    return result.to_json()


class WebhookRouter():
  __handlers: dict[str, EventHandler] = {}

  def bind(self, env: BoundEnv, logger: Logger) -> BoundRouter:
    return BoundRouter(self.__handlers, env, logger)

  def _wrap_func(self, func):
    def result(env, data):
      sig = inspect.signature(func)
      final_data = dict(data)
      # if we don't have a kwargs field, remove any extra attributes from the args map
      if len([v for v in sig.parameters.values() if v.kind == inspect.Parameter.VAR_KEYWORD]) == 0:
        for k in data.keys():
          if k not in sig.parameters.keys():
            del final_data[k]

      # if there's an env parameter, inject our environment state
      env_param = sig.parameters.get("env", None)
      if env_param and env_param.annotation == BoundEnv:
        final_data["env"] = env

      # then call the actual handler
      return func(**final_data)
    return result

  def handler(self, event: str) -> Callable:
    """
    Decorator, function plus event name
    """
    def decorator(func):
      if event in self.__handlers:
        raise f"Already registered a handler for {event}!"

      self.__handlers[event] = self._wrap_func(func)
      return func
    return decorator

  def by_action(self, event: str) -> Callable[[str], Callable[[EventHandler], EventHandler]]:
    """
    Return a value that can be used as a decorator to dispatch handlers
    for ``event`` based on the provided action.
    """

    dispatchers: dict[str, EventHandler] = {}

    def subhandler(env, data) -> Optional[EmbedBody]:
      action = data.get("action", None)
      if action not in dispatchers:
        return None
      return dispatchers[action](env, data)

    def decorator_wrap(action: str) -> Callable[[EventHandler], EventHandler]:
      def decorator(func: EventHandler) -> EventHandler:
        if action in dispatchers:
          raise f"Already registered a subhandler for {action} (in {event}!"

        dispatchers[action] = self._wrap_func(func)
        return func
      return decorator

    self.__handlers[event] = subhandler

    return decorator_wrap
