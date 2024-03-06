from django.db import models
from django.contrib.auth.models import AbstractUser

# CustomUser - add in_game_name as required field and full-name field 
class CustomUser(AbstractUser):
    in_game_name = models.CharField(
        max_length=20, unique=True, verbose_name="ingame name")
    full_name = models.CharField(
        max_length=100, verbose_name="full name")
    

    def __str__(self):
        return self.username


# Teams / Relationships / invitations

class Team(models.Model):
    creator = models.OneToOneField(
        CustomUser, related_name='created_team', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='team_logos/')
    created_at = models.DateTimeField(auto_now_add=True)


class TeamMembership(models.Model):
    ROLE_CHOICES = (
        ('Player', 'Player'),
        ('Captain', 'Captain'),
    )

    player = models.OneToOneField(
        CustomUser, related_name='team_membership', on_delete=models.CASCADE)
    team = models.ForeignKey(
        Team, related_name='memberships', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('team', 'role')

    def __str__(self):
        return f"{self.player.full_name}'s membership in {self.team.name} as {self.role}"


class Invitation(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    )

    sender = models.ForeignKey(
        CustomUser, related_name='sent_invitations', on_delete=models.CASCADE)
    team = models.ForeignKey(
        Team, related_name='invitations', on_delete=models.CASCADE)
    receiver = models.OneToOneField(
        CustomUser, related_name='received_invitations', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invitation from {self.sender.full_name} to {self.receiver.full_name} for team {self.team.name}"
