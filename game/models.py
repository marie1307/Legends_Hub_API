from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from django.utils import timezone
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

# CustomUser - add in_game_name as required field and full-name field 
class CustomUser(AbstractUser):
    in_game_name = models.CharField(max_length=20, unique=True, verbose_name="ingame name")
    full_name = models.CharField(
        max_length=100, verbose_name="full name")    

    def __str__(self):
        return self.username

    
# Team
class Team(models.Model):
    creator = models.ForeignKey(CustomUser, related_name='created_teams', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False, verbose_name="Is Complete")
    member_count = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class TeamRole(models.Model):
    MAIN_ROLE_CHOICES = (
        ('Top lane', 'Top lane'),
        ('Mid lane', 'Mid lane'),
        ('Jungle', 'Jungle'),
        ('Bot lane', 'Bot lane'),
        ('Support', 'Support'),
    )
    SUB_ROLE_CHOICES = (
        ('Sub player 1', 'Sub player 1'),
        ('Sub player 2', 'Sub player 2'),
    )
    team = models.ForeignKey(Team, related_name='roles', on_delete=models.CASCADE)
    member = models.ForeignKey(CustomUser, related_name='team_roles', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=MAIN_ROLE_CHOICES + SUB_ROLE_CHOICES)

    class Meta:
        unique_together = ('team', 'member', 'role')

    def __str__(self):
        return f"{self.member.in_game_name} as {self.role} in {self.team.name}"


@receiver(pre_save, sender=TeamRole)
def limit_team_members(sender, instance, **kwargs):
    # Check if a TeamRole with the same team, member, and role already exists.
    if TeamRole.objects.filter(team=instance.team, member=instance.member, role=instance.role).exists():
        raise ValidationError(
            "A member can only have one unique role in the same team.")

@receiver(post_save, sender=TeamRole)
def update_team_status(sender, instance, **kwargs):
    team = instance.team
    # Count unique main roles in the team
    main_roles_count = team.roles.filter(role__in=[role[0] for role in TeamRole.MAIN_ROLE_CHOICES]).values('role').distinct().count()
    # Check if team has 5 unique main roles
    if main_roles_count == len(TeamRole.MAIN_ROLE_CHOICES):
        team.status = True
    else:
        team.status = False
    team.member_count = team.roles.count()
    team.save()


class Invitation(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    )
    sender = models.ForeignKey(
        CustomUser, related_name='sent_invitations', on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        CustomUser, related_name='received_invitations', on_delete=models.CASCADE)
    team = models.ForeignKey(
        Team, related_name='invitations', on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=TeamRole.MAIN_ROLE_CHOICES + TeamRole.SUB_ROLE_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver', 'team', 'role')

    def __str__(self):
        return f"Invitation from {self.sender.full_name} to {self.receiver.full_name} for role {self.role} in team {self.team.name}"


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message

# Tournamens
class Tournament(models.Model):
    title = models.CharField(max_length=255)
    created_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.title
    
# Registraion on tournament    
class TournamentRegistration(models.Model):
    tournament = models.ForeignKey('Tournament', related_name='registrations', on_delete=models.CASCADE)
    team = models.ForeignKey('Team', related_name='tournament_registrations', on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)


# Games history
class Game(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='games')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='games')
    score = models.IntegerField(default=0)
    win = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    total_game = models.IntegerField(default=0)
    registered_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.team} in {self.tournament} collected {self.score} score in {self.total_game} games"


# Games schedule
class GameSchedule(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='schedules')
    time = models.DateTimeField()
    team_1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='game_schedules_team_1')
    team_2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='game_schedules_team_2')
    score_team_1 = models.IntegerField(default=0)
    score_team_2 = models.IntegerField(default=0)
    image_team_1 = models.ImageField(upload_to='team_photos/', blank=True, null=True)
    image_team_2 = models.ImageField(upload_to='team_photos/', blank=True, null=True)
    vote = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.team_1}'s and {self.team_2}'s game has {self.vote} votes"
