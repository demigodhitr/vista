from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta
from app.models import Investments, Profiles, EarningsHistory, LossesHistory, TradingParameters
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import random
import logging

logger = logging.getLogger('django')

class Command(BaseCommand):
    help = 'Auto Increase profits for active investments'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = now.date()
        active_investments = Investments.objects.filter(status='Active')

        if today.weekday() in [5, 6]:
            print("It's weekend, profits will not be updated, updates continue on the start of a new week")
            return

        if active_investments:
            print('Active investments found, updating profits...')
            for investment in active_investments:
                investment_start = investment.date.date()
                elapsed_days = (today - investment_start).days

                if investment.days_remaining is None:
                    investment.days_remaining = investment.duration - elapsed_days

                # Decrease days_remaining counter if it's a new day
                if investment.last_decrement != today and investment.days_remaining > 0:
                    investment.days_remaining = max(investment.duration - elapsed_days, 0)
                    investment.last_decrement = today
                    investment.save()
                    print(f'Decremented days_remaining for investment with ID: {investment.pk}. {investment.days_remaining} days remaining.')

                try:
                    duration_days = int(investment.duration)
                    investment_start = investment.date
                    investment_end = investment_start + timedelta(days=duration_days)

                    if now > investment_end:
                        # Investment duration completed
                        investment.status = 'Completed'
                        investment.save()
                        profile = investment.investor.profiles
                        profile.trade_status = 'Completed'
                        profile.alert_user = True
                        profile.save()

                    # Calculate total profit target
                    parameter = TradingParameters.objects.filter(investment=investment).first()
                    rate = parameter.profit_target if parameter else Decimal('11')
                    profit_target = investment.amount * rate
                    total_intervals = max(duration_days * 24, 1)
                    profit_per_interval = (profit_target / Decimal(total_intervals)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                    print('Calculated total profit target')

                    # Calculate elapsed intervals
                    elapsed_time = now - investment_start
                    elapsed_hours = elapsed_time.total_seconds() // 3600
                    intervals_passed = int(elapsed_hours)
                    print(f'Hours passed: {intervals_passed}')

                    # Expected total profit
                    expected_total_profit = profit_per_interval * Decimal(intervals_passed)
                    print(f"Expected total profit: {expected_total_profit}")

                    # Fetch the investor's profile
                    profile = investment.investor.profiles

                    # Calculate the difference to update
                    profit_difference = expected_total_profit - profile.profits

                    # Simulate profits or losses
                    if random.uniform(0, 1) <= 0.7:  # 70% chance for profit
                        profit_change = profit_difference
                        change_type = "profit"
                    else:
                        # Reduce profits for losses
                        profit_change = -abs(profit_difference * Decimal('0.05'))  # 5% loss on profit
                        change_type = "loss"

                    if profit_change != 0:
                        with transaction.atomic():
                            if change_type == "profit":
                                if expected_total_profit > profile.profits:
                                    profile.profits += profit_change
                                    EarningsHistory.objects.create(
                                        user=investment.investor,
                                        investment=investment,
                                        profit_amount=profit_change,
                                        timestamp=now
                                    )
                                    print(
                                        f'Profits recorded in the Earnings History table: \n'
                                        f'Increased profits for {investment.investor.username} by {profit_difference}\n\n\n'
                                    )
                                else:
                                    profit_change = Decimal('20.23') if investment.waiver else Decimal('50.00')
                                    
                                    if profile.profits - expected_total_profit < Decimal('200.00'):
                                        profile.profits += profit_change
                                        EarningsHistory.objects.create(
                                            user=investment.investor,
                                            investment=investment,
                                            profit_amount=profit_change,
                                            timestamp=now
                                        )


                            elif change_type == "loss":
                                # Deduct loss amount directly from profits
                                profile.profits -= abs(profit_change)
                                LossesHistory.objects.create(
                                    user=investment.investor,
                                    investment=investment,
                                    loss_amount=abs(profit_change),
                                    timestamp=now
                                )
                                print(f'Recorded loss for {investment.investor.username} of {abs(profit_change)}\n\n')

                            investment.last_updated = now
                            investment.save()

                except Exception as e:
                    logger.exception(f'Failed to run management command on {investment.investor.username} profile at {timezone.now()}')
                    self.stderr.write(f'Error processing investment {investment.id}: {e}')
                    send_mail(
                        'Profit Increment Error',
                        f'An error occurred while processing investment ID {investment.id} for user {investment.investor.username}: {e}',
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_EMAIL],
                        fail_silently=False,
                    )
        else:
            print('No active investments found')
            logger.info('No active investment at this time')
