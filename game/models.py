from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# CustomUser - add in_game_name as required field and full-name field 
class CustomUser(AbstractUser):
    in_game_name = models.CharField(
        max_length=20, unique=True, verbose_name="ingame name")
    full_name = models.CharField(
        max_length=100, verbose_name="full name")
    

    def __str__(self):
        return self.username


# Teams / Relationships / invitations
    
# Team
class Team(models.Model):
    creator = models.OneToOneField(CustomUser, related_name='captain', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    member_count = models.PositiveSmallIntegerField(default=0)

# Team membership
class TeamMembership(models.Model):
    player = models.OneToOneField(CustomUser, related_name='team_membership', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='memberships', on_delete=models.CASCADE)
    member_status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.player.full_name}'s membership in {self.team.name} is {self.member_status}"

# Invitations
class Invitation(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    )
    
    sender = models.ForeignKey(CustomUser, related_name='sent_invitations', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, related_name='invitations', on_delete=models.CASCADE)
    receiver = models.ForeignKey(CustomUser, related_name='received_invitations', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation from {self.sender.full_name} to {self.receiver.full_name} for team {self.team.name}"


# Notifications
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message
