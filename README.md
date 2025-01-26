# pydisgit

pydisgit is a port of the [disgit](https://github.com/JRoy/disgit) tool to Python on a [Quart](https://quart.palletsprojects.com/en/latest/)/ASGI stack. As with the original, pydisgit is a webook proxy for sending GitHub messages to Discord that provides higher quality results than the built-in GitHub endpoint that Discord offers.

This additionally leaves it fully independent of the Cloudflare environment, and lets us use the (subjectively) superior and more reliable Python ecosystem.

## usage

pydisgit is published as a Docker image ready to go under `ghcr.io/kyoripowered/pydisgit:latest`.

### environment variables

pydisgit has the following optional environment variables that you can use to customize your instance:

- `PYDISGIT_IGNORED_BRANCHES_REGEX` - A regex pattern for branches that should be ignored
- `PYDISGIT_IGNORED_BRANCHES` - A comma seperated list of branches that should be ignored
- `PYDISGIT_IGNORED_USERS` - A comma seperated list of users that should be ignored
- `PYDISGIT_IGNORED_PAYLOADS` - A comma seperated list of webhook events that should be ignored

### deployment

Some example unit files for deployment under Podman Quadlet with systemd socket activation behind an Ngnix reverse proxy are provided in the `[etc/deployment](etc/deployment) folder. By default, the docker image will bind to port 8000 if it's used on its own.

We recommend choosing a webhook secret to prevent unauthorized users from exhausting the host server's available ratelimit space.

## licensing

pydisgit is released under the terms of the Apache Software License version 2.0. Thanks additionally go out to JRoy and all other contributors to upstream disgit for making it what it is today.

## Supported Events

The following webhook events are supported as of now:

* [check_run](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#check_run)
* [commit_comment](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#commit_comment)
* [create](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#create)
* [delete](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#delete)
* [deployment](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#deployment)
* [deployment_status](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#deployment_status)
* [discussion](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#discussion)
* [discussion_comment](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#discussion_comment)
* [fork](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#fork)
* [gollum](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#gollum) (wiki)
* [issue_comment](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#issue_comment)
  * This event also sends pull request comments...*sigh*
* [issues](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#issues)
* [package](https://docs.github.com/en/webhooks-and-events/webhooks/webhook-events-and-payloads#package)
* [ping](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#ping)
* [pull_request](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request)
* [pull_request_review](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request_review)
* [pull_request_review_comment](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#pull_request_review_comment)
* [push](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#push)
* [release](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#release)
* [star](https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#star)
* ...feel free to contribute more that suit your needs!
