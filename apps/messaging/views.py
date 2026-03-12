from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Thread, Message
from .forms import MessageForm, NewThreadForm

User = get_user_model()


@login_required
def inbox(request):
    """Show all threads this user is part of."""
    threads = request.user.threads.prefetch_related(
        'participants', 'messages'
    ).order_by('-updated_at')
    return render(request, 'messaging/inbox.html', {'threads': threads})


@login_required
def thread_detail(request, pk):
    """Show messages in a thread; mark unread messages as read."""
    thread = get_object_or_404(
        Thread.objects.prefetch_related('messages__sender', 'participants'),
        pk=pk,
        participants=request.user,
    )

    # Mark all messages not sent by me as read
    thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.thread = thread
            msg.sender = request.user
            msg.save()
            # Bump thread's updated_at so it sorts to top of inbox
            thread.save()
            return redirect('messaging:thread-detail', pk=thread.pk)

    return render(request, 'messaging/thread_detail.html', {
        'thread': thread,
        'form': form,
    })


@login_required
def new_thread(request, username):
    """Start a new conversation with a user (e.g. from a listing page)."""
    recipient = get_object_or_404(User, username=username)

    if recipient == request.user:
        messages.error(request, "You can't message yourself.")
        return redirect('marketplace:listing-list')

    # Check if a thread already exists between these two users
    existing = Thread.objects.filter(
        participants=request.user
    ).filter(participants=recipient).first()

    if existing:
        return redirect('messaging:thread-detail', pk=existing.pk)

    form = NewThreadForm(request.POST or None)
    if form.is_valid():
        subject = form.cleaned_data.get('subject', '')
        body = form.cleaned_data['body']
        thread = Thread.objects.create(subject=subject)
        thread.participants.add(request.user, recipient)
        Message.objects.create(thread=thread, sender=request.user, body=body)
        messages.success(request, f"Message sent to {recipient.username}.")
        return redirect('messaging:thread-detail', pk=thread.pk)

    return render(request, 'messaging/new_thread.html', {
        'form': form,
        'recipient': recipient,
    })
