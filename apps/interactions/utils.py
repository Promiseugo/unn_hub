from django.contrib.contenttypes.models import ContentType
from django.db.models import CharField, Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Cast, Coalesce, Replace

from .models import Comment, Reaction


OWNER_FIELD_BY_MODEL = {
    ("marketplace", "listing"): "seller_id",
    ("services", "serviceoffer"): "provider_id",
    ("rentals", "rentallisting"): "landlord_id",
}


def get_owner_id(obj):
    key = (obj._meta.app_label, obj._meta.model_name)
    owner_field = OWNER_FIELD_BY_MODEL.get(key)
    return getattr(obj, owner_field, None) if owner_field else None


def is_content_owner(user, obj):
    if not user.is_authenticated:
        return False
    return get_owner_id(obj) == user.pk


def should_count_view(request, obj):
    if is_content_owner(request.user, obj):
        return False

    object_key = f"{obj._meta.app_label}.{obj._meta.model_name}:{obj.pk}"
    viewed = set(request.session.get("viewed_content", []))
    if object_key in viewed:
        return False

    viewed.add(object_key)
    request.session["viewed_content"] = sorted(viewed)
    if hasattr(request.session, "modified"):
        request.session.modified = True
    return True


def with_interaction_counts(queryset, model):
    content_type = ContentType.objects.get_for_model(model)
    object_id = Replace(
        Cast(OuterRef("pk"), output_field=CharField()),
        Value("-"),
        Value(""),
    )

    like_counts = (
        Reaction.objects
        .filter(content_type=content_type, reaction_type=Reaction.LIKE)
        .annotate(normalized_object_id=Replace("object_id", Value("-"), Value("")))
        .filter(normalized_object_id=object_id)
        .values("object_id")
        .annotate(total=Count("pk"))
        .values("total")[:1]
    )
    comment_counts = (
        Comment.objects
        .filter(content_type=content_type, is_active=True, parent=None)
        .annotate(normalized_object_id=Replace("object_id", Value("-"), Value("")))
        .filter(normalized_object_id=object_id)
        .values("object_id")
        .annotate(total=Count("pk"))
        .values("total")[:1]
    )

    return queryset.annotate(
        like_count=Coalesce(Subquery(like_counts, output_field=IntegerField()), Value(0)),
        comment_count=Coalesce(Subquery(comment_counts, output_field=IntegerField()), Value(0)),
    )
