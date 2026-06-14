from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django_ratelimit.decorators import ratelimit
from .models import Thread, Message
from .forms import MessageForm, NewThreadForm
from .services import create_moderated_message
from apps.trust.utils import log_audit

User = get_user_model()


@login_required
def unread_count(request):
    count = Message.objects.filter(
        thread__participants=request.user,
        is_read=False,
    ).exclude(sender=request.user).count()
    return JsonResponse({'unread_count': count})


@login_required
def inbox(request):
    """Show all threads enriched with other-participant and unread count."""
    threads = request.user.threads.prefetch_related(
        'participants', 'messages'
    ).order_by('-updated_at')

    # Pre-compute other participant and unread count per thread
    # so templates don't need to call methods with arguments
    thread_data = []
    for thread in threads:
        other = thread.participants.exclude(pk=request.user.pk).first()
        unread = thread.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
        thread_data.append({
            'thread': thread,
            'other': other,
            'unread': unread,
            'last_message': thread.messages.last(),
        })

    return render(request, 'messaging/inbox.html', {'thread_data': thread_data})


@login_required
@ratelimit(key='user_or_ip', rate='20/m', method='POST', block=True)
def thread_detail(request, pk):
    thread = get_object_or_404(
        Thread.objects.prefetch_related('messages__sender', 'participants'),
        pk=pk,
        participants=request.user,
    )

    # Mark messages from others as read
    thread.messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    other = thread.participants.exclude(pk=request.user.pk).first()

    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = create_moderated_message(
                request=request,
                thread=thread,
                sender=request.user,
                body=form.cleaned_data['body'],
            )
            thread.save()   # bump updated_at
            log_audit(request, 'message_sent', msg, metadata={'thread_id': thread.pk})
            return redirect('messaging:thread-detail', pk=thread.pk)

    return render(request, 'messaging/thread_detail.html', {
        'thread': thread,
        'other': other,
        'form': form,
    })


@login_required
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def new_thread(request, username):
    recipient = get_object_or_404(User, username=username)

    if recipient == request.user:
        messages.error(request, "You can't message yourself.")
        return redirect('marketplace:listing-list')

    # Reuse existing thread if one exists
    existing = Thread.objects.filter(
        participants=request.user
    ).filter(participants=recipient).first()

    if existing:
        return redirect('messaging:thread-detail', pk=existing.pk)

    form = NewThreadForm(request.POST or None)
    if form.is_valid():
        thread = Thread.objects.create(
            subject=form.cleaned_data.get('subject', '')
        )
        thread.participants.add(request.user, recipient)
        create_moderated_message(
            request=request,
            thread=thread,
            sender=request.user,
            body=form.cleaned_data['body'],
        )
        messages.success(request, f"Message sent to {recipient.username}.")
        return redirect('messaging:thread-detail', pk=thread.pk)

    return render(request, 'messaging/new_thread.html', {
        'form': form,
        'recipient': recipient,
    })
