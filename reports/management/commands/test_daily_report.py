from django.core.management.base import BaseCommand
from reports.management.commands.send_daily_report import (
    Command as SendDailyReportCommand,
)


class Command(BaseCommand):
    help = "Test daily report generation for all accounts without sending email"

    def handle(self, *args, **options):
        # Create instance of send daily report command
        send_report_cmd = SendDailyReportCommand()
        send_report_cmd.stdout = self.stdout

        try:
            # Generate daily report data for all businesses
            all_reports_data = send_report_cmd.generate_all_business_reports()

            # Display report summary for all businesses
            self.stdout.write("=" * 60)
            self.stdout.write("DAILY REPORTS TEST - ALL ACCOUNTS")
            self.stdout.write("=" * 60)

            for report_data in all_reports_data:
                self.stdout.write(f"Business: {report_data['business'].company_name}")
                self.stdout.write(
                    f"Report Period: {report_data['start_date']} to {report_data['end_date']}"
                )
                self.stdout.write("-" * 40)
                self.stdout.write("SUMMARY:")
                self.stdout.write(f"  Total Sales: ${report_data['total_sales']:.2f}")
                self.stdout.write(f"  Total Orders: {report_data['total_orders']}")
                self.stdout.write(
                    f"  Total Expenses: ${report_data['total_expenses']:.2f}"
                )
                self.stdout.write(f"  Net Profit: ${report_data['net_profit']:.2f}")
                self.stdout.write("-" * 40)
                self.stdout.write("TOP SELLING PRODUCTS:")
                for product in report_data["top_products"]:
                    self.stdout.write(
                        f"  - {product['product__name']}: {product['total_sold']} units (${product['total_revenue']:.2f})"
                    )
                self.stdout.write("-" * 40)
                self.stdout.write("RECOMMENDATIONS:")
                for rec in report_data["recommendations"]:
                    priority = rec.get("priority", "medium").upper()
                    self.stdout.write(f"  [{priority}] {rec.get('title', '')}")
                    self.stdout.write(f"      {rec.get('description', '')}")
                    self.stdout.write(f"      Action: {rec.get('action', '')}")
                    self.stdout.write("")
                self.stdout.write("=" * 60)

            self.stdout.write(
                self.style.SUCCESS(
                    "Daily reports generation test for all accounts completed successfully!"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to generate daily reports for all accounts: {str(e)}"
                )
            )
