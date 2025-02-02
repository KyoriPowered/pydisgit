"""
Configuration for pydisgit
"""

import re
from typing import Optional


class Config:
  """
  Raw environment from Workers
  """

  IGNORED_BRANCH_REGEX: str = "^$"
  IGNORED_BRANCHES: str = ""
  IGNORED_USERS: str = ""
  IGNORED_PAYLOADS: str = ""

  # secrets
  PASTE_GG_API_KEY: Optional[str] = None
  GITHUB_WEBHOOK_SECRET: Optional[str] = None


class BoundEnv:
  """
  Parsed + bound environment
  """

  __ignored_branch_pattern: re.Pattern
  __ignored_branches: list[str]
  __ignored_users: list[str]
  __ignored_payloads: list[str]
  __pastegg_api_key: str
  __github_webhook_secret: str

  def __init__(self, env, logger):
    self.__ignored_branch_pattern = (
      re.compile(env["IGNORED_BRANCH_REGEX"]) if "IGNORED_BRANCH_REGEX" in env else None
    )
    self.__ignored_branches = env["IGNORED_BRANCHES"].split(",")
    self.__ignored_users = env["IGNORED_USERS"].split(",")
    self.__ignored_payloads = env["IGNORED_PAYLOADS"].split(",")
    self.__pastegg_api_key = env["PASTE_GG_API_KEY"]
    self.__github_webhook_secret = env["GITHUB_WEBHOOK_SECRET"]

    logger.info("Ignored branch pattern: %s", self.__ignored_branch_pattern)
    logger.info("Ignored branches: %s", self.__ignored_branches)
    logger.info("Ignored users: %s", self.__ignored_users)
    logger.info("Ignored payloads: %s", self.__ignored_payloads)

  def ignored_branch(self, branch: str) -> bool:
    return (
      self.__ignored_branch_pattern and self.__ignored_branch_pattern.match(branch)
    ) or branch in self.__ignored_branches

  def ignored_user(self, user: str) -> bool:
    return user in self.__ignored_users

  def ignored_payload(self, payload: str) -> bool:
    return payload in self.__ignored_payloads

  @property
  def github_webhook_secret(self) -> str:
    return self.__github_webhook_secret

  async def build_debug_paste(self, embed: any) -> str:
    pass


#     embed = JSON.stringify({
#       "files": [
#         {
#           "content": {
#             "format": "text",
#             "value": embed
#           }
#         }
#       ]
#     });
#
#     embed = await (await fetch("https://api.paste.gg/v1/pastes", {
#       "headers": {
#         "user-agent": "disgit (kyori flavor)",
#         "content-type": "application/json",
#         "Authorization": f'Key {self.__pastegg_api_key}'
#       },
#       "method": "POST",
#       "body": embed
#     })).text();
#
#     embed = JSON.stringify({
#       "content": embed
#     });
#     return embed;
