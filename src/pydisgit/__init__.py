from httpx import AsyncClient
import pprint
from quart import Quart, Response, request
from werkzeug.exceptions import BadRequest

from .conf import Config, BoundEnv

Quart.__annotations__["http_client"] = AsyncClient
app = Quart(__name__)


# config setup
app.config.from_object(Config)
app.config.from_prefixed_env(prefix="PYDISGIT")

bound = BoundEnv(app.config, app.logger)

from .handlers import router as free_handler_router
handler_router = free_handler_router.bind(bound, app.logger)

# http client

@app.before_serving
async def setup_httpclient():
  app.http_client = AsyncClient(
    headers={'User-Agent': 'pydisgit (kyori flavour)'}
  )

@app.after_serving
async def teardown_httpclient():
  await app.http_client.aclose()

@app.get('/')
async def hello() -> str:
  """
  root handler
  """
  return "begone foul beast", 400


@app.post('/<hook_id>/<token>')
async def gh_hook(hook_id: str, token: str) -> dict:
  event = request.headers["X-GitHub-Event"]
  if not event or not request.content_type:
    raise BadRequest("No event or content type")

  #if (!(await validateRequest(request, env.githubWebhookSecret))) {
  #  return new Response('Invalid secret', { status: 403 });
  #}

  if "application/json" in request.content_type:
    json = await request.json
  elif "application/x-www-form-urlencoded" in request.content_type:
    json = json.loads((await request.form)['payload'])
  else:
    raise BadRequest(f"Unknown content type {request.content_type}")

  embed = handler_router.process_request(event, json)
  if not embed:
    return 'Webhook NO-OP', 200

  if app.config['DEBUG']:
    pprint.pprint(embed)
    pass
    # embed = await bound.buildDebugPaste(embed)

  http: AsyncClient = app.http_client

  result = await http.post(f"https://discord.com/api/webhooks/{hook_id}/{token}", json = embed)

  if result.status_code == 200:
    result_text = "".join([await a async for a in result.aiter_text()])
    return {"message": f"We won! Webhook {hook_id} executed with token {token} :3, response: {result_text}"}, 200
  else:
    return Response(response = await result.aread(), status = result.status_code, content_type=result.headers)


@app.get('/health')
async def health_check() -> str:
  """
  simple aliveness check
  """
  return "OK"


def run_dev() -> None:
  """
  Run a development instance of the app
  """
  app.run()
