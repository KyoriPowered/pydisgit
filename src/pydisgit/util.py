from dataclasses import dataclass
from hmac import HMAC
import re
from typing import NamedTuple, Optional

__NEWLINE_REGEXP = re.compile(r"<!--(?:.|\n|\r)*?-->[\n|\r]*")


def truncate(text: str, num: int) -> Optional[str]:
  if not text:
    return None

  text = __NEWLINE_REGEXP.sub("", text)
  if len(text) <= num:
    return text

  return text[0:num - 3] + "..."


def short_commit(hash: str) -> str:
  return hash[0:7]


# make into middleware
async def validate_request(request, secret: str) -> bool:
  pass
#   signature_header = request.headers.get("X-Hub-Signature-256")?.substring("sha256=".length);
#
#  if not signature_header: return False
#  const hmac = createHmac("sha256", secret);
#  hmac.update(await request.bytes());
#  return signatureHeader == hmac.digest('hex');
