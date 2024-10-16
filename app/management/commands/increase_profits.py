from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta
from app.models import Investments, Profiles, EarningsHistory
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

import logging

logger = logging.getLogger('django')

class Command(BaseCommand):
    help = 'Auto Increase profits for active investments'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = now.date()
        active_investments = Investments.objects.filter(status='Active')

        if today.weekday() in [5, 6]:
            print ('It\'s weekend, profits will not be updated, updates continues on the start of a new week')
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
                        profile.save()
                        try:
                            subject = 'Congratulations! Your trade has been completed'
                            template = 'trade-completed.html'
                            html_content = render_to_string(template, {'userprofile': profile})
                            text_content = strip_tags(html_content)
                            email = EmailMultiAlternatives(
                                subject,
                                text_content,
                                settings.DEFAULT_FROM_EMAIL,
                                [investment.investor.email],
                            )
                            email.attach_alternative(html_content, "text/html")
                            email.send()
                            print(f'Completed investment {investment.pk} for user {investment.investor.username}')
                        except Exception as e:
                            logger.exception(f'"Error sending email to {investment.investor.email}", ERROR:{e}')
                            continue

                    # Calculate total profit target
                    profit_target = investment.amount * Decimal('9')  # 10x growth
                    total_intervals = duration_days * 24  # hourly intervals
                    profit_per_interval = (profit_target / Decimal(total_intervals)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                    print('Calculated total profit target')

                    # Calculate elapsed intervals
                    elapsed_time = now - investment_start
                    elapsed_hours = elapsed_time.total_seconds() // 3600
                    intervals_passed = int(elapsed_hours)
                    print('Calculated elapsed intervals')

                    # Expected total profit
                    expected_total_profit = profit_per_interval * Decimal(intervals_passed)
                    print(expected_total_profit)

                    # Fetch the associated profile
                    profile = investment.investor.profiles

                    # Calculate the difference to update
                    profit_difference = expected_total_profit - profile.profits

                    if profit_difference > 0:
                        with transaction.atomic():
                            profile.profits += profit_difference
                            profile.save()

                            EarningsHistory.objects.create(
                                user=investment.investor,
                                investment=investment,
                                profit_amount=profit_difference,
                                timestamp=timezone.now()
                            )
                            print('Increment recorded in the Earnings History table....')

                            investment.last_updated = now
                            investment.save()
                            print(f'Increased profits for {investment.investor.username} by {profit_difference}')
                            logger.info(f'Increased profits for {investment.investor.username} by {profit_difference}')


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