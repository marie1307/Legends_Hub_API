from django.core.management.base import BaseCommand
from django.db import transaction
from game.models import Tournament, GameSchedule
import random

class Command(BaseCommand):
    help = 'Generate game schedules for tournaments'

    @transaction.atomic
    def handle(self, *args, **options):
        # Iterate over all tournaments or filter as needed
        for tournament in Tournament.objects.all():
            self.stdout.write(f"Processing {tournament.title}")

            # Fetch all registered teams for the tournament
            registered_teams = list(tournament.teams.all())
            
            # Ensure there is an even number of teams
            if len(registered_teams) % 2 != 0:
                self.stdout.write("Odd number of teams, one team will not be scheduled.")
                registered_teams.pop()  # Remove one team, or handle differently

            # Shuffle teams to randomize matchups
            random.shuffle(registered_teams)

            # Create game schedules
            for i in range(0, len(registered_teams), 2):
                team_1 = registered_teams[i]
                team_2 = registered_teams[i + 1]
                
                # # Create a GameSchedule instance for each pair
                # GameSchedule.objects.create(
                #     tournament=tournament,
                #     time=random.choice([time for time in a predefined time list]),  # Placeholder, define your logic
                #     team_1=team_1,
                #     team_2=team_2
                # )

            self.stdout.write(f"Finished scheduling games for {tournament.title}")
