"""Quest Test"""
from django.test import TransactionTestCase
from django.contrib.auth.models import User
from apps.managers.challenge_mgr import challenge_mgr
from apps.utils import test_utils

from apps.widgets.quests.quests import get_quests, possibly_completed_quests
from apps.widgets.quests.models import Quest, QuestMember


class QuestTest(TransactionTestCase):
    """Quest Test"""
    def setUp(self):
        challenge_mgr.init()
        self.user = User(username="testuser", password="password")
        self.user.save()

    def testGetQuests(self):
        """Tests that we can get the quests for a user."""
        # Create some sample quests.
        self.assertEqual(len(get_quests(self.user)["available_quests"]), 0,
            "There are no quests for the user.")
        for i in range(0, 3):
            quest_name = "Test Quest %d" % i
            quest = Quest(
                name=quest_name,
                quest_slug="test_quest_%d" % i,
                description=quest_name,
                priority=1,
                unlock_conditions="True",
                completion_conditions="False"  # User cannot complete these.
            )
            quest.save()

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 3, "User should have 3 quests available.")

        # Test that if we add another quest, the user still has the 3 original quests.
        quest = Quest(
            name="Another quest",
            quest_slug="another_quest",
            description="another quest",
            priority=1,
            unlock_conditions="True",
            completion_conditions="False",
        )
        quest.save()

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 3,
            "User should still have 3 quests available.")
        self.assertTrue(quest not in quests, "New quest should not be in quests.")

        # Mark a quest as completed so that the new quest is picked up.
        quests["available_quests"][0].accept(self.user)
        member = QuestMember.objects.filter(user=self.user)[0]
        member.completed = True
        member.save()

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 3, "User should have 3 quests available.")
        self.assertTrue(quest in quests["available_quests"], "New quest should be in quests.")

    def testOptOut(self):
        """Test that once a user opts out of a quest, it doesn't show up."""
        quest = Quest(
            name="Another quest",
            quest_slug="another_quest",
            description="another quest",
            priority=1,
            unlock_conditions="False",  # User cannot unlock this quest
            completion_conditions="False",
        )
        quest.save()

        self.assertFalse(quest.opt_out(self.user), "User should not be able to see this quest.")

        quest.unlock_conditions = "True"
        quest.save()
        self.assertTrue(quest.opt_out(self.user), "User should be able to opt out of this quest.")

        quests = get_quests(self.user)
        self.assertTrue(quest not in quests["available_quests"],
            "User should not see the quest as available.")
        self.assertTrue(quest not in quests["user_quests"],
            "User should not have this listed as their current quest.")

    def testAccept(self):
        """Test that the user can accept quests."""
        quest = Quest(
            name="Another quest",
            quest_slug="another_quest",
            description="another quest",
            priority=1,
            unlock_conditions="False",  # User cannot unlock this quest
            completion_conditions="False",
        )
        quest.save()

        self.assertFalse(quest.accept(self.user), "User should not be able to accept this quest.")
        self.assertEqual(self.user.quest_set.count(), 0, "User should not have any quests.")

        quest.unlock_conditions = "True"
        quest.save()
        self.assertTrue(quest.accept(self.user), "User should be able to accept this quest.")
        self.assertEqual(self.user.quest_set.count(), 1, "User should have an accepted quest.")

    def testBasicPrerequisites(self):
        """Tests that the user can only get quests for which they meet the prerequisites."""
        quest = test_utils.create_quest(completion_conditions=False)
        quest.unlock_conditions = "False"
        quest.save()

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 0,
            "User should not have this quest available.")

        quest.unlock_conditions = "True"
        quest.save()
        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 1, "User should now have one quest.")

    def testBasicCompletion(self):
        """Tests that the user can complete quests."""
        quest = test_utils.create_quest(completion_conditions=False)

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 1, "User should have one quest.")

        quests["available_quests"][0].accept(self.user)

        possibly_completed_quests(self.user)
        complete_quests = self.user.quest_set.filter(questmember__completed=True)
        self.assertTrue(quest not in complete_quests, "Quest should not be completed.")

        quest.completion_conditions = True
        quest.save()
        possibly_completed_quests(self.user)
        complete_quests = self.user.quest_set.filter(questmember__completed=True)
        self.assertTrue(quest in complete_quests,
            "Quest should be in the user's complete quests list.")

        quests = get_quests(self.user)
        self.assertTrue(quest not in quests["available_quests"],
            "Quest should not be available after completion.")
        self.assertTrue(quest not in quests["user_quests"],
            "Quest should not be in the user's active quests.")

    def testCommentsAreIgnored(self):
        """Tests that any comments in the text are ignored."""
        quest = Quest(
            name="Test quest",
            quest_slug="test_quest",
            description="test quest",
            priority=1,
            unlock_conditions="#Hello World\nTrue",
            completion_conditions="#Hello World\nFalse",
        )
        quest.save()

        quests = get_quests(self.user)
        self.assertEqual(len(quests["available_quests"]), 1, "User should now have one quest.")

        quests["available_quests"][0].accept(self.user)

        quest.completion_conditions = "#Hello World\nTrue"
        quest.save()

        possibly_completed_quests(self.user)
        complete_quests = self.user.quest_set.filter(questmember__completed=True)
        self.assertTrue(quest in complete_quests,
            "Quest should be in the user's complete quests list.")
