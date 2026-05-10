import json
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Reaction, Comment


def _get_ct_and_object(app_label, model_name, object_id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    try:
        obj = ct.get_object_for_this_type(pk=object_id)
    except Exception:
        return None, None, None
    return ct, obj, object_id


def _redirect_to_object(obj):
    if hasattr(obj, 'get_absolute_url'):
        return redirect(obj.get_absolute_url())
    return redirect('marketplace:listing-list')


# ── Reactions ────────────────────────────────────────────────
@login_required
@require_POST
def react(request, app_label, model_name, object_id):
    """Toggle or switch like/dislike. Returns JSON for AJAX calls."""
    ct, obj, _ = _get_ct_and_object(app_label, model_name, object_id)
    if obj is None:
        return JsonResponse({'error': 'Not found'}, status=404)

    try:
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
    except (json.JSONDecodeError, AttributeError):
        reaction_type = request.POST.get('reaction_type')

    if reaction_type not in ('like', 'dislike'):
        return JsonResponse({'error': 'Invalid reaction'}, status=400)

    existing = Reaction.objects.filter(
        user=request.user,
        content_type=ct,
        object_id=str(object_id),
    ).first()

    if existing:
        if existing.reaction_type == reaction_type:
            # Same button clicked again — remove reaction
            existing.delete()
            action = 'removed'
        else:
            # Switch reaction
            existing.reaction_type = reaction_type
            existing.save()
            action = 'switched'
    else:
        Reaction.objects.create(
            user=request.user,
            content_type=ct,
            object_id=str(object_id),
            reaction_type=reaction_type,
        )
        action = 'added'

    likes    = Reaction.objects.filter(content_type=ct, object_id=str(object_id), reaction_type='like').count()
    dislikes = Reaction.objects.filter(content_type=ct, object_id=str(object_id), reaction_type='dislike').count()

    user_reaction = None
    r = Reaction.objects.filter(user=request.user, content_type=ct, object_id=str(object_id)).first()
    if r:
        user_reaction = r.reaction_type

    return JsonResponse({
        'action': action,
        'likes': likes,
        'dislikes': dislikes,
        'user_reaction': user_reaction,
    })


# ── Comments ─────────────────────────────────────────────────
@login_required
@require_POST
def add_comment(request, app_label, model_name, object_id):
    ct, obj, _ = _get_ct_and_object(app_label, model_name, object_id)
    if obj is None:
        return JsonResponse({'error': 'Not found'}, status=404)

    body = request.POST.get('body', '').strip()
    parent_id = request.POST.get('parent_id', '').strip()

    if not body:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)
    if len(body) > 1000:
        return JsonResponse({'error': 'Comment too long (max 1000 characters)'}, status=400)

    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(
                pk=parent_id,
                content_type=ct,
                object_id=str(object_id),
                is_active=True,
                parent=None,  # only allow one level of threading
            )
        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Parent comment not found'}, status=400)

    comment = Comment.objects.create(
        user=request.user,
        content_type=ct,
        object_id=str(object_id),
        body=body,
        parent=parent,
    )

    return JsonResponse({
        'id': comment.pk,
        'body': comment.body,
        'user': comment.user.username,
        'created_at': comment.created_at.strftime('%b %d, %Y'),
        'is_reply': comment.is_reply,
        'parent_id': parent.pk if parent else None,
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, user=request.user)
    comment.is_active = False
    comment.save()
    return JsonResponse({'deleted': True})
