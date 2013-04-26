"""Notification testing."""

from django.test import TransactionTestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from apps.managers.challenge_mgr import challenge_mgr
from apps.utils import test_utils

from apps.widgets.notifications import get_unread_notifications
from apps.widgets.notifications.models import UserNotification


class NotificationUnitTests(TransactionTestCase):
    """Notification Test."""
    def testGetUnread(self):
        """Test that we can get the user's unread notifications."""
        user = User.objects.create_user("test", "test@test.com")
        for i in range(0, 3):
            notification = UserNotification(recipient=user, contents="Test notification %i" % i)
            notification.save()

        notifications = get_unread_notifications(user)
        self.assertEqual(notifications["alerts"].count(), 0,
            "There should not be any alert notifications.")
        unread = notifications["unread"]
        self.assertEqual(unread.count(), 3, "There should be three unread notifications.")
        alert = UserNotification(recipient=user, contents="Alert notification", display_alert=True)
        alert.save()

        notifications = get_unread_notifications(user)
        self.assertEqual(notifications["alerts"][0], alert,
            "Alert notification should have been returned.")
        unread = notifications["unread"]
        self.assertEqual(unread.count(), 4, "There should be four unread notifications.")


class NotificationFunctionalTests(TransactionTestCase):
    """View Test."""

    def setUp(self):
        self.user = test_utils.setup_user(username="user", password="test")
        self.team = self.user.get_profile().team

        challenge_mgr.register_page_widget("help", "help.faq")
        challenge_mgr.register_page_widget("home", "home")

        from apps.managers.cache_mgr import cache_mgr
        cache_mgr.clear()

        self.client.login(username="user", password="test")

    def testShowNotifications(self):
        """
        Test that we can show notifications to the user.
        """
        for i in range(0, 3):
            notification = UserNotification(recipient=self.user,
                contents="Test notification %i" % i)
            notification.save()

        response = self.client.get(reverse("home_index"))
        self.assertNotContains(response, "The following item(s) need your attention",
            msg_prefix="Alert should not be shown"
        )
        for i in range(0, 3):
            self.assertContains(response, "Test notification %i" % i,
                msg_prefix="Notification %i is not shown" % i
            )

    def testAlertNotifications(self):
        """Test alert."""
        alert = UserNotification(recipient=self.user, contents="Alert notification",
            display_alert=True)
        alert.save()
        response = self.client.get(reverse("home_index"))
        self.assertContains(response, "notification-dialog", msg_prefix="Alert should be shown")

        response = self.client.get(reverse("help_index"))
        self.assertNotContains(response, "notification-dialog",
            msg_prefix="Dialog should not be displayed")

    def testAjaxReadNotifications(self):
        """Test that notifications can be marked as read via AJAX."""
        notification = UserNotification(recipient=self.user, contents="Test notification")
        notification.save()

        response = self.client.post(reverse("notifications_read", args=(notification.pk,)), {},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("home_index"))
        self.assertNotContains(response, "Test notification",
            msg_prefix="Notification should be read")

    def testReadNotifications(self):
        """Test that notifications can be marked as read without AJAX."""
        notification = UserNotification(recipient=self.user, contents="Test notification")
        notification.save()

        response = self.client.post(reverse("notifications_read", args=(notification.pk,)), {})
        self.assertRedirects(response, reverse("home_index"),
            msg_prefix="Marking as read should redirect.")

        response = self.client.get(reverse("home_index"))
        self.assertNotContains(response, "Test notification",
            msg_prefix="Notification should be read")

        # Test with a referring page.
        notification = UserNotification(recipient=self.user, contents="Test notification 2")
        notification.save()

        response = self.client.post(reverse("notifications_read", args=(notification.pk,)), {},
            HTTP_REFERER=reverse("help_index"))
        self.assertRedirects(response, reverse("help_index"),
            msg_prefix="Marking as read should redirect.")

        response = self.client.get(reverse("home_index"))
        self.assertNotContains(response, "Test notification 2",
            msg_prefix="Notification should be read")
