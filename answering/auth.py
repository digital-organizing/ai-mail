from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from answering.models import OutputWebhook


def get_auth(webhook: OutputWebhook):
    match webhook.auth_type:
        case "digest":
            return HTTPDigestAuth(webhook.auth_user, webhook.auth_credential)
        case "basic":
            return HTTPBasicAuth(webhook.auth_user, webhook.auth_credential)

    return None
