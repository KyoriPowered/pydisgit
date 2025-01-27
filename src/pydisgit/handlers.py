"""
GH event handlers
"""
import logging

from .conf import BoundEnv
from .util import short_commit, truncate
from .webhook import EmbedBody, Field, WebhookRouter

__slots__ = ['router']

logger = logging.getLogger(__name__)
router = WebhookRouter()

@router.handler('ping')
def ping(zen, hook, repository, sender, organization=None) -> EmbedBody:
  is_org = hook['type'] == 'Organization'
  name =  organization['login'] if is_org else repository['full_name']

  return EmbedBody(
    f'[{name}] {hook['type']} hook ping received',
    None,
    sender,
    0xb8e98c,
    zen
  )


check_run_action = router.by_action("check_run")

@check_run_action('completed')
# @router.filter(test = BoundEnv.ignored_branch, path = ['check_run', 'check_suite', 'head_branch']) # would this ever be nicer? than injecting the env as a parameter
def check_completed(env: BoundEnv, check_run, repository, sender) -> EmbedBody:
  conclusion = check_run["conclusion"]
  output = check_run["output"]
  html_url = check_run["html_url"]
  check_suite = check_run["check_suite"]

  if not repository or not (target := check_suite["head_branch"]):
    logger.debug("No repo or no target (%s) for check run", target)
    return None

  if env.ignored_branch(target):
    logger.debug("ignoring branch %s", target)
    return None

  if len(check_suite["pull_requests"]):
    pull = check_suite["pull_requests"][0]
    if pull.url.startsWith(f'https://api.github.com/repos/{repository["full_name"]}'):
      target = f'PR #{pull.number}'

  color = 0xaaaaaa
  status = "failed"
  match conclusion:
    case "success":
      color = 0x00b32a
      status = "succeeded"
    case "failure" | "cancelled":
      color = 0xff3b3b
      status = "failed" if conclusion == "failure" else  "cancelled"
    case "timed_out" | "action_required" | "stale":
      color = 0xe4a723
      match conclusion:
        case "timed_out": status = "timed out"
        case "action_required": status = "requires action"
        case _: status = "stale"
    case "neutral":
      status = "didn't run"
    case "skipped":
      status = "was skipped"

  fields = [
    Field(name='Action Name', value = check_run["name"])
  ]

  if "title" in output and output["title"]:
    fields.append(Field(name="Output Title", value=output["title"]))

  if "summary" in output and output["summary"]:
    fields.append(Field(name="Output Summary", value=output["summary"]))

  return EmbedBody(
    f"[{repository["full_name"]}] Actions check {status} on {target}",
    html_url,
    sender,
    color,
    fields=fields
  )

commit_comment = router.by_action('commit_comment')

@commit_comment('created')
def commit_comment_created(env: BoundEnv, sender, comment, repository):
  if env.ignored_user(sender["login"]):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] New comment on commit `{short_commit(comment["commit_id"])}`",
    comment["html_url"],
    sender,
    0x000001,
    comment["body"]
  )


@router.handler('create')
def create_branch(env: BoundEnv, ref, ref_type, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  if ref_type == "branch" and env.ignored_branch(ref):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] New {ref_type} created: {ref}",
    None,
    sender,
    0x000001
  )


@router.handler('delete')
def delete_branch(env: BoundEnv, ref, ref_type, repository, sender):
  if ref_type == "branch" and env.ignored_branch(ref):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] {ref_type} deleted: {ref}",
    None,
    sender,
    0x000001
  )


discussion_action = router.by_action('discussion')


@discussion_action('created')
def discussion_created(env: BoundEnv, discussion, repository, sender):
  if env.ignored_user(sender.login):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] New discussion: #{discussion["number"]} {discussion["title"]}",
    discussion["html_url"],
    sender,
    0x9494ff,
    discussion["body"],
    f"Discussion Category: {discussion["category"]["name"]}"
  )


discussion_comment_action = router.by_action('discussion_comment')


@discussion_comment_action('created')
def discussion_comment_created(env: BoundEnv, discussion, comment, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] New comment on discussion: #{discussion["number"]} {discussion["title"]}",
    comment["html_url"],
    sender,
    0x008a76,
    comment.body,
    f"Discussion Category: {discussion["category"]["name"]}"
  )


@router.handler("fork")
def fork(sender, repository, forkee):
  return EmbedBody(
    f"[{repository["full_name"]}] Fork Created: {forkee["full_name"]}",
    forkee["html_url"],
    sender,
    0xfcb900
  )

issue_comment_action = router.by_action('issue_comment')

@issue_comment_action('created')
def issue_comment_created(env: BoundEnv, issue, comment, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  entity = "pull request" if "pull_request" in issue else "issue"
  return EmbedBody(
    f"[{repository["full_name"]}] New comment on {entity}: #{issue["number"]} {issue["title"]}",
    comment["html_url"],
    sender,
    0xad8b00,
    comment["body"]
  )


issues_action = router.by_action('issues')


@issues_action('opened')
def issues_opened(env: BoundEnv, issue, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  return EmbedBody(
    f"[{repository["full_name"]}] Issue opened: #{issue["number"]} {issue["title"]}",
    issue["html_url"],
    sender,
    0xff7d00,
    issue["body"]
  )


@issues_action('reopened')
def issues_reopened(issue, repository, sender):
  return EmbedBody(
    f"[{repository["full_name"]}] Issue reopened: #{issue["number"]} {issue["title"]}",
    issue["html_url"],
    sender,
    0xff7d00
  )


@issues_action('closed')
def issues_closed(issue, repository, sender):
  return EmbedBody(
    f"[{repository["full_name"]}] Issue closed: #{issue["number"]} {issue["title"]}",
    issue["html_url"],
    sender,
    0xff482f
  )


package_action = router.by_action('package')


@package_action('published')
def package_published(sender, repository, package=None, registry_package=None):
  pkg = package if package else registry_package

  return EmbedBody(
    f"[{repository["full_name"]}] Package Published: {pkg["namespace"]}/{pkg["name"]}",
    pkg["package_version"]["html_url"],
    sender,
    0x009202
  )


@package_action('updated')
def package_updated(sender, repository, package=None, registry_package=None):
  pkg = package if package else registry_package

  return EmbedBody(
    f"[{repository["full_name"]}] Package Updated: {pkg["namespace"]}/{pkg["name"]}",
    pkg["package_version"]["html_url"],
    sender,
    0x9202
  )


pull_request_action = router.by_action('pull_request')


@pull_request_action('opened')
def pull_request_opened(env: BoundEnv, pull_request, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  draft = pull_request["draft"]
  color = 0xa7a7a7 if draft else 0x009202
  pr_type = "Draft pull request" if draft else "Pull request"

  return EmbedBody(
    f"[{repository["full_name"]}] {pr_type} opened: #{pull_request["number"]} {pull_request["title"]}",
    pull_request["html_url"],
    sender,
    color
  )

@pull_request_action('closed')
def pull_request_closed(pull_request, repository, sender):
  merged = pull_request["merged"]
  color = 0x8748ff if merged else 0xff293a
  status = "merged" if merged else "closed"

  return EmbedBody(
    f"[{repository["full_name"]}] Pull request {status}: #{pull_request["number"]} {pull_request["title"]}",
    pull_request["html_url"],
    sender,
    color
  )

@pull_request_action('reopened')
def pull_request_reopened(env: BoundEnv, pull_request, repository, sender):
  if env.ignored_user(sender["login"]):
    return None

  draft = pull_request["draft"]
  color = 0xa7a7a7 if draft else 0x009202
  pr_type = "Draft pull request" if draft else "Pull request"

  return EmbedBody(
    f"[{repository["full_name"]}] {pr_type} reopened: #{pull_request["number"]} {pull_request["title"]}",
    pull_request["html_url"],
    sender,
    color
  )

@pull_request_action('converted_to_draft')
def pull_request_converted_to_draft(pull_request, repository, sender):
  return EmbedBody(
    f"[{repository["full_name"]}] Pull request marked as draft: #{pull_request["number"]} {pull_request["title"]}",
    pull_request["html_url"],
    sender,
    0xa7a7a7
  )

@pull_request_action('ready_for_review')
def pull_request_ready_for_review(pull_request, repository, sender):
  return EmbedBody(
    f"[{repository["full_name"]}] Pull request marked for review: #{pull_request["number"]} {pull_request["title"]}",
    pull_request["html_url"],
    sender,
    0x009202
  )

pull_request_review_action = router.by_action('pull_request_review')

@pull_request_review_action('submitted')
@pull_request_review_action('dismissed')
def pull_request_review(pull_request, review, repository, action, sender):
  state = "reviewed"
  color = 7829367

  match review["state"]:
    case "approved":
      state = "approved"
      color = 37378
    case "changes_requested":
      state = "changes requested"
      color = 16722234
    case _:
      if action == "dismissed":
        state = "review dismissed"

  return EmbedBody(
    f"[{repository["full_name"]}] Pull request {state}: #{pull_request["number"]} {pull_request["title"]}",
    review["html_url"],
    sender,
    color,
    review["body"]
  )

pull_request_review_comment_action = router.by_action('pull_request_review_comment')


@pull_request_review_comment_action('created')
def pull_request_review_comment_created(pull_request, comment, repository, sender):
  return EmbedBody(
    f"[{repository["full_name"]}] Pull request review comment: #{pull_request["number"]} {pull_request["title"]}",
    comment["html_url"],
    sender,
    0x777777,
    comment["body"]
  )

@router.handler('push')
def push(env: BoundEnv, commits, forced, after, repository, ref, compare, sender):
  branch = ref[11:]

  if env.ignored_branch(branch):
    return None
  if env.ignored_user(sender["login"]):
    return None

  if forced:
    return EmbedBody(
      f"[{repository["full_name"]}] Branch {branch} was force-pushed to `{short_commit(after)}`",
      compare.replace("...", ".."),
      sender,
      0xff293a
    )

  amount = len(commits)
  if amount == 0:
    return None

  description = ""
  last_commit_url = ""
  for commit in commits:
    commit_url = commit["url"]
    line = f"[`{short_commit(commit["id"])}`]({commit_url}) {truncate(commit["message"].split("\n")[0], 50)} - {commit["author"]["username"]}\n"
    if (len(description) + len(line)) >= 1500:
      break

    last_commit_url = commit_url
    description += line

  commit_word = "commit" if amount == 1 else "commits"

  return EmbedBody(
    f"[{repository["name"]}:{branch}] {amount} new {commit_word}",
    last_commit_url if amount == 1 else compare,
    sender,
    0x5d62e4,
    description
  )

release_action = router.by_action('release')

@release_action('released')
@release_action('prereleased')
def release_released(release, repository, sender):
  if release["draft"]:
    return None

  effective_name = release.get("name", None)
  if not effective_name:
    effective_name = release["tag_name"]

  return EmbedBody(
    f"[{repository['full_name']}] New {'pre' if release["prerelease"] else ''}release published: {effective_name}",
    release["html_url"],
    sender,
    0xde5de4,
    release["body"]
  )

star_action = router.by_action('star')

@star_action('created')
def star_created(sender, repository):
  return EmbedBody(
    f"[{repository["full_name"]}] New star added",
    repository["html_url"],
    sender,
    0xfcb900
  )

deployment_action = router.by_action('deployment')

@deployment_action('created')
def deployment_created(deployment, repository, sender):
  web_url = deployment["payload"].get("web_url")
  if not web_url:
    web_url = ""

  return EmbedBody(
    f"[{repository["full_name"]}] Deployment started for {deployment["description"]}",
    web_url,
    sender,
    0xaa44b9
  )

@router.handler('deployment_status')
def deployment_status(deployment, deployment_status, repository, sender):
  web_url = deployment["payload"].get("web_url")
  if not web_url:
    web_url = ""

  color = 0xff3b3b
  term = "succeeded"
  match deployment_status["state"]:
    case "success":
      color = 0x00b32a
    case "failure":
      term = "failed"
    case "error":
      term = "errored"
    case _:
      return None

  return EmbedBody(
    f"[{repository["full_name"]}] Deployment for {deployment["description"]} {term}",
    web_url,
    sender,
    color
  )

@router.handler("gollum")
def gollum(pages, sender, repository):
  # Pages is always an array with several "actions".
  # Count the amount of "created" and "edited" actions and store the amount in a variable.
  # Also store the titles of the pages in an array since we will need them later.
  created = 0
  edited = 0
  titles: list[str] = []
  for page in pages:
    action = page["action"]
    if action == "created":
      created += 1
    elif action == "edited":
      edited += 1

    # Wrap the title in a markdown with the link to the page.
    title = f"[{page["title"]}](${page["html_url"]})"

    # Capitalize the first letter of the action, then prepend it to the title.
    titles.insert(0, f"{action[0].upper() + action[1:]}: {title}")

  # Set the message based on if there are any created or edited pages.
  # If there are only 1 of one type, set the message to singular.
  # If there are multiple of one type, set the message to plural.
  message = ""
  color = 6120164
  match (created, edited):
    case (0, 0):
      # If there are no pages, return null.
      return None
    case (1, 0):
      message = "A page was created"
      # Set the color to green.
      color = 0x00b32a
    case (0, 1):
      message = "A page was edited"
      # Set the color to orange.
      color = 0xfcb900
    case (a, b) if a > 0 and b > 0:
      message = f"{created} page{"s" if created > 1 else ""} were created and {edited} {"were" if edited > 1 else "was"} edited"
    case _:
      message = f"{max(created, edited)} pages were {"created" if created > 0 else "edited"}"

  # Prepend the repository title to the message.
  message = f"[{repository["full_name"]}] {message}"

  # Build the embed, with the sender as the author, the message as the title, and the edited pages as the description.
  return EmbedBody(
    message,
    repository["html_url"],
    sender,
    color,
    "\n".join(titles),
  )
