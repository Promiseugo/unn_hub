from apps.trust.utils import contains_contact_info, log_suspicious, redact_contact_info

from .models import Message


def build_moderated_message_payload(*, request, thread, sender, body):
    payload = {
        'thread': thread,
        'sender': sender,
        'body': body,
        'original_body': body,
    }
    if contains_contact_info(body):
        payload['body'] = redact_contact_info(body)
        payload['moderation_status'] = Message.STATUS_FLAGGED
        payload['moderation_reasons'] = ['Contact information redacted']
        log_suspicious(
            request,
            'message_contact_redacted',
            'Message contained direct contact information and was redacted.',
            severity='low',
            metadata={'thread_id': thread.pk},
        )
    return payload


def create_moderated_message(*, request, thread, sender, body):
    return Message.objects.create(
        **build_moderated_message_payload(
            request=request,
            thread=thread,
            sender=sender,
            body=body,
        )
    )
